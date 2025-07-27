# backend/app/api/routers/parking.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date, timedelta, datetime
from fastapi import Query
import math

from app import database, schemas
from app import api_schemas
from app.api.deps import get_db

router = APIRouter(prefix="/parking_violations", tags=["Parking Violations"])

@router.get("/", response_model=List[schemas.ParkingViolationData])
def get_parking_violations(
     skip: int=0, 
     limit: int=100, 
     branch_id: Optional[str]=None, 
     db: Session=Depends(get_db)
     ):
    query = db.query(database.DBParkingViolation)
    if branch_id:
        query = query.filter(database.DBParkingViolation.branch_id.startswith(branch_id))
    return query.offset(skip).limit(limit).all()

#--- ข้อมูลสรุป KPI Card, Chart, Top Branch---#
@router.get(
    "/summary",
    response_model=api_schemas.ViolationSummaryResponse,
    summary="Get Aggregated Summary of Parking Violations"
)
def get_violation_summary(
    db: Session = Depends(get_db),
    branch_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    group_by_unit: str = 'day'
):
    """
    Endpoint นี้จะคำนวณและรวบรวมข้อมูลสรุปทั้งหมดสำหรับหน้า Parking Violations:
    1.  คำนวณ KPI Cards
    2.  คำนวณข้อมูลสำหรับ Chart (จัดกลุ่มรายวัน)
    3.  คำนวณ Top 5 สาขาที่มีการละเมิดสูงสุด
    """
    # ถ้าไม่มีการส่งวันที่มา ให้ใช้ Default เป็น 7 วันล่าสุด
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=6)

    # สร้าง Base Query เพื่อเป็นตัวตั้งต้น    
    base_query = db.query(database.DBParkingViolation)

    # เงื่อนไข .filter() เข้าไปใน Base Query ถ้ามีการส่งค่ามา
    if branch_id:
        base_query = base_query.filter(database.DBParkingViolation.branch_id.startswith(branch_id))
    if start_date:
        base_query = base_query.filter(database.DBParkingViolation.timestamp >= start_date)
    if end_date:
        from datetime import timedelta
        # บวกไป 1 วันเพื่อให้ครอบคลุมข้อมูลของ end_date ทั้งวัน
        base_query = base_query.filter(database.DBParkingViolation.timestamp < (end_date + timedelta(days=1)))

    # --- 1. คำนวณข้อมูลสำหรับ KPI Cards ---

    total_unique_branches = base_query.with_entities(func.count(database.DBParkingViolation.branch_id.distinct()))\
        .scalar() or 0
    
    # online_threshold = datetime.utcnow() - timedelta(minutes=15)
    # online_branches_count = db.query(func.count(database.DBParkingViolation.branch_id.distinct()))\
    #     .filter(database.DBParkingViolation.timestamp >= online_threshold)\
    #     .scalar() or 0
    
    total_violations = base_query.filter(database.DBParkingViolation.is_violation == True).count()
    ongoing_violations = base_query.filter(
        database.DBParkingViolation.is_violation == True,
        database.DBParkingViolation.exit_time.is_(None)
    ).count()

    avg_duration_violation = base_query.with_entities(func.avg(database.DBParkingViolation.duration_minutes)).filter(database.DBParkingViolation.is_violation == True).scalar() or 0
    avg_duration_normal = base_query.with_entities(func.avg(database.DBParkingViolation.duration_minutes)).filter(database.DBParkingViolation.is_violation == False).scalar() or 0
    total_sessions = base_query.count()

    kpi_data = api_schemas.ParkingKpiData(
        totalViolations=total_violations,
        ongoingViolations=ongoing_violations,
        total_parking_sessions=total_sessions,
        avgViolationDuration=round(avg_duration_violation, 1),
        avgNormalParkingTime=round(avg_duration_normal, 1),
        onlineBranches=total_unique_branches
    )

    # --- 2. คำนวณข้อมูลสำหรับ Violations Chart (ตัวอย่าง: จัดกลุ่มรายวัน 30 วันล่าสุด) ---

    chart_base_query = base_query.filter(database.DBParkingViolation.is_violation == True)

    chart_data = []
    
    if group_by_unit == 'hour':
        results_db = chart_base_query.with_entities(
            func.strftime('%H', database.DBParkingViolation.timestamp).label("label"),
            func.count(database.DBParkingViolation.id).label("count")
        ).group_by("label").all()
        results_map = {f"{int(r.label):02d}:00": r.count for r in results_db}
        for hour in range(24):
            hour_str = f"{hour:02d}:00"
            chart_data.append(api_schemas.ViolationChartDataPoint(label=hour_str, value=results_map.get(hour_str, 0)))

    elif group_by_unit == 'day':
        results_db = chart_base_query.with_entities(
            func.date(database.DBParkingViolation.timestamp).label("label"),
            func.count(database.DBParkingViolation.id).label("count")
        ).group_by("label").all()
        results_map = {str(r.label): r.count for r in results_db}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            chart_data.append(api_schemas.ViolationChartDataPoint(label=date_str, value=results_map.get(date_str, 0)))
            current_date += timedelta(days=1)
            
    elif group_by_unit == 'week':
        # ใช้ %Y-%W สำหรับ SQLite เพื่อให้ได้ 'ปี-เลขสัปดาห์'
        results_db = chart_base_query.with_entities(
            func.strftime('%Y-%W', database.DBParkingViolation.timestamp).label("label"),
            func.count(database.DBParkingViolation.id).label("count")
        ).group_by("label").all()
        results_map = {r.label: r.count for r in results_db}
        
        current_date = start_date
        while current_date <= end_date:
            week_label = current_date.strftime("%Y-%W")
            # เพิ่มข้อมูลสัปดาห์เข้าไปถ้ายังไม่มี
            if not any(d.label == week_label for d in chart_data):
                chart_data.append(api_schemas.ViolationChartDataPoint(label=week_label, value=results_map.get(week_label, 0)))
            # เลื่อนไปสัปดาห์ถัดไป
            current_date += timedelta(days=7)

    elif group_by_unit == 'month':
        # 1. ดึงข้อมูลจริงจาก DB
        results_db = chart_base_query.with_entities(
            func.strftime('%Y-%m', database.DBParkingViolation.timestamp).label("label"),
            func.count(database.DBParkingViolation.id).label("count")
        ).group_by("label").all()
        results_map = {r.label: r.count for r in results_db}
        
        # 2. สร้างข้อมูลเปล่าสำหรับทุกเดือนในช่วงที่เลือก
        current_year = start_date.year
        current_month = start_date.month
        
        # วนลูปจนกว่าจะเลย end_date
        while date(current_year, current_month, 1) <= end_date:
            month_label = f"{current_year}-{current_month:02d}"
            # เติมข้อมูลจาก DB หรือใส่ 0 ถ้าไม่มี
            chart_data.append(api_schemas.ViolationChartDataPoint(label=month_label, value=results_map.get(month_label, 0)))

            # เลื่อนไปยังเดือนถัดไป
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

    # --- 3. คำนวณ Top 5 Branches ---
    top_branches_query_base = db.query(database.DBParkingViolation)
    if start_date:
        top_branches_query_base = top_branches_query_base.filter(database.DBParkingViolation.timestamp >= start_date)
    if end_date:
        from datetime import timedelta
        top_branches_query_base = top_branches_query_base.filter(database.DBParkingViolation.timestamp < (end_date + timedelta(days=1)))
 
    top_branches_query = top_branches_query_base.with_entities(
        database.DBParkingViolation.branch,
        database.DBParkingViolation.branch_id,
        func.count(database.DBParkingViolation.id).label("violation_count")
    ).filter(database.DBParkingViolation.is_violation == True,
             database.DBParkingViolation.branch.isnot(None))\
     .group_by(database.DBParkingViolation.branch, database.DBParkingViolation.branch_id)\
     .order_by(func.count(database.DBParkingViolation.id).desc())\
     .limit(5).all()

    top_branches_data = [api_schemas.TopBranchData(name=row.branch, code=row.branch_id, count=row.violation_count) for row in top_branches_query]

    # --- 4. รวบรวมข้อมูลทั้งหมดและส่งกลับในรูปแบบที่กำหนด ---
    return api_schemas.ViolationSummaryResponse(
        kpi=kpi_data,
        chart_data=chart_data,
        top_branches=top_branches_data
    )

#--- ดึงข้อมูลสาขาทั้งหมดแบบแบ่งหน้า---#
@router.get(
    "/all_branches",
    response_model=api_schemas.PaginatedTopBranchResponse,
    summary="Get a paginated list of all violating branches"
)
def get_all_violating_branches(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    query_base = db.query(database.DBParkingViolation)\
        .filter(database.DBParkingViolation.is_violation == True)\
        .filter(database.DBParkingViolation.branch.isnot(None))

    if start_date:
        query_base = query_base.filter(database.DBParkingViolation.timestamp >= start_date)
    if end_date:
        from datetime import timedelta
        query_base = query_base.filter(database.DBParkingViolation.timestamp < (end_date + timedelta(days=1)))
    
    subquery = query_base.group_by(
        database.DBParkingViolation.branch_id
    ).subquery()

    # Query เพื่อนับจำนวนกลุ่มทั้งหมด (ก่อน limit)
    total_items_query = query_base.group_by(
        database.DBParkingViolation.branch, 
        database.DBParkingViolation.branch_id
    )
    total_items = db.query(func.count(subquery.c.id)).scalar()
    total_pages = math.ceil(total_items / limit)

    # Query เพื่อดึงข้อมูลของหน้านั้นๆ
    branches_query = query_base.with_entities(
        database.DBParkingViolation.branch,
        database.DBParkingViolation.branch_id,
        func.count(database.DBParkingViolation.id).label("violation_count")
    ).group_by(
        database.DBParkingViolation.branch,
        database.DBParkingViolation.branch_id
    ).order_by(
        func.count(database.DBParkingViolation.id).desc()
    ).offset((page - 1) * limit).limit(limit).all()

    branches_data = [
        api_schemas.TopBranchData(name=row.branch, code=row.branch_id, count=row.violation_count) 
        for row in branches_query
    ]

    return api_schemas.PaginatedTopBranchResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        branches=branches_data
    )

#--- ข้อมูลตารางทั้งหมด---#
@router.get(
    "/events",
    response_model=api_schemas.PaginatedViolationEventsResponse,
    summary="Get Paginated and Transformed Parking Violation Events"
)
def get_violation_events(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    branch_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_violation_only: bool = False
):
    """
    Endpoint นี้จะดึงข้อมูลเหตุการณ์แบบแบ่งหน้าสำหรับแสดงในตาราง
    และแปลงโครงสร้างข้อมูลให้ตรงตามที่ Frontend ต้องการ
    """
    query = db.query(database.DBParkingViolation)

    if branch_id:
        query = query.filter(database.DBParkingViolation.branch_id.startswith(branch_id))
    if start_date:
        query = query.filter(database.DBParkingViolation.timestamp >= start_date)
    if end_date:
        from datetime import timedelta
        query = query.filter(database.DBParkingViolation.timestamp < (end_date + timedelta(days=1)))
    if is_violation_only:
        query = query.filter(database.DBParkingViolation.is_violation == True)

    # นับจำนวนรายการทั้งหมด (ก่อนที่จะแบ่งหน้า)
    total_items = query.count()

    # คำนวณจำนวนหน้าทั้งหมด
    total_pages = math.ceil(total_items / limit)

    # 1. ดึงข้อมูลดิบจากฐานข้อมูล พร้อมการแบ่งหน้า
    #    - order_by: เรียงจากเหตุการณ์ล่าสุดไปเก่าสุด
    #    - offset: ข้ามข้อมูลของหน้าก่อนๆ
    #    - limit: จำกัดจำนวนข้อมูลต่อหน้า
    db_violations = query.order_by(database.DBParkingViolation.timestamp.desc())\
        .offset((page - 1) * limit)\
        .limit(limit)\
        .all()
    
    # 2. แปลงข้อมูล (Transformation) ทีละรายการ
    #    นี่คือส่วนที่แปลงข้อมูลจาก ORM Model (DBParkingViolation)
    #    ไปเป็น Pydantic Schema (ParkingViolationEvent) ที่ออกแบบไว้สำหรับ Frontend
    results = []
    for v in db_violations:
        event = api_schemas.ParkingViolationEvent(
            id=v.id,
            status="Violate" if v.is_violation else "Normal",
            timestamp=v.timestamp,
            branch=api_schemas.BranchInfo(id=v.branch_id, name=v.branch),
            camera=api_schemas.CameraInfo(id=v.camera_id),
            vehicleId=str(v.car_id),
            entryTime=v.entry_time,
            exitTime=v.exit_time,
            durationMinutes=v.duration_minutes,
            isViolation=v.is_violation,
            total_parking_sessions=v.total_parking_sessions or 0,
            imageBase64=v.image_base64
        )
        results.append(event)
    
    # 3. ส่งข้อมูลที่แปลงร่างแล้วกลับไป
    return api_schemas.PaginatedViolationEventsResponse(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        events=results
    )