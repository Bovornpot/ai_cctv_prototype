# main.py
from contextlib import asynccontextmanager
from typing import List, Optional, Dict 
from datetime import datetime, timedelta, time 
import pytz 
from sqlalchemy import func
import logging
import asyncio 
# ### เพิ่ม ###: Import Header และ Depends สำหรับ API Key (FEATURE 5)
from fastapi import FastAPI, Depends, HTTPException, status, Query, Header 
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func # Import func for aggregate functions
import schemas
import database

thailand_tz = pytz.timezone('Asia/Bangkok')
# Configure logging for this Worker Process (โค้ดเดิม)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
last_hourly_summary_check_time: Optional[datetime] = None 

# ### เพิ่ม ###: ฟังก์ชันและตัวแปรสำหรับตรวจสอบ API Key (FEATURE 5)
# ในระบบจริง ควรดึงค่านี้มาจาก Environment Variable เพื่อความปลอดภัย
EXPECTED_API_KEY = "nemo1234" 

async def verify_api_key(x_api_key: str = Header(...)):
    """Dependency function to verify the API key from the request header."""
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

# --- Lifespan Context Manager (โค้ดเดิม) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global last_hourly_summary_check_time 

    logger.info("Application startup: Initializing database tables and other services...")
    database.create_db_tables()
    logger.info("Database tables ensured and ready.")

    with next(get_db()) as db_session:
        last_summary_record = db_session.query(database.DBParkingViolation.timestamp)\
                                        .filter(database.DBParkingViolation.event_type == "hourly_summary")\
                                        .order_by(database.DBParkingViolation.timestamp.desc())\
                                        .first()
        if last_summary_record:
            utc_naive_dt = last_summary_record[0]
            utc_aware_dt = utc_naive_dt.replace(tzinfo=pytz.utc)
            last_hourly_summary_check_time = utc_aware_dt.astimezone(thailand_tz)
            logger.info(f"Loaded last_hourly_summary_check_time from DB (converted to TH Time): {last_hourly_summary_check_time}")
        else:
            last_hourly_summary_check_time = datetime.now(thailand_tz).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            logger.info(f"Initial last_hourly_summary_check_time set (no DB record): {last_hourly_summary_check_time}")

    yield 

    logger.info("Application shutdown: Stopping services and cleaning up...")
    logger.info("Application shutdown complete.")

# --- FastAPI App Initialization (โค้ดเดิม) ---
app = FastAPI(
    title="AI CCTV Prototype Backend API",
    description="API for receiving and serving AI inference results from CCTV streams.",
    version="0.1.0",
    lifespan=lifespan 
)

# --- CORS Middleware (โค้ดเดิม) ---
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Dependency (โค้ดเดิม) ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Root Endpoint (โค้ดเดิม) ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint that returns a simple HTML welcome page for API status check."""
    return """
    <html>
        <head>
            <title>AI CCTV Prototype API</title>
        </head>
        <body>
            <h1>Welcome to AI CCTV Prototype Backend API!</h1>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation (Swagger UI).</p>
            <p>Visit <a href="/redoc">/redoc</a> for alternative API documentation.</p>
            <p>Check API health at <a href="/health">/health</a>.</p>
        </body>
    </html>
    """
# --- Health Check Endpoint (โค้ดเดิม) ---
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Endpoint for checking API status."""
    return {"status": "ok", "message": "API is healthy and operational!"}

# --- Analytics Data Ingestion Endpoint ---
# ### แก้ไข ###: เพิ่ม `dependencies=[Depends(verify_api_key)]` เพื่อบังคับให้ทุก request ต้องมี API Key ที่ถูกต้อง (FEATURE 5)
@app.post("/analytics", status_code=status.HTTP_201_CREATED,
    response_model=schemas.InferenceResultResponse,
    summary="Receive Analytics Data (Parking Violation, Table Occupancy, Chilled Basket Alert)",
    dependencies=[Depends(verify_api_key)]
)
async def create_inference_result(
    data: schemas.AnalyticsDataIn,
    db: Session = Depends(get_db)
):
    logger.info(f"Received analytics data for processing.") 

    try:
        db_item = None
        message = "No valid analytics data provided."

        if data.parking_violation:
            pv_data = data.parking_violation

            if pv_data.timestamp.tzinfo is None:
                timestamp_aware_utc = thailand_tz.localize(pv_data.timestamp).astimezone(pytz.utc)
            else:
                timestamp_aware_utc = pv_data.timestamp.astimezone(pytz.utc)

            db_item = database.DBParkingViolation( 
                timestamp=timestamp_aware_utc,
                branch=pv_data.branch,
                branch_id=pv_data.branch_id,
                camera_id=pv_data.camera_id,
                event_type=pv_data.event_type, 
                car_id=pv_data.car_id,
                current_park=pv_data.current_park, 
                entry_time=pv_data.entry_time.astimezone(pytz.utc) if pv_data.entry_time else None,
                exit_time=pv_data.exit_time.astimezone(pytz.utc) if pv_data.exit_time else None,
                duration_minutes=pv_data.duration_minutes,
                is_violation=pv_data.is_violation,
                total_parking_sessions=pv_data.total_parking_sessions, 
                # ### เพิ่ม ###: เพิ่มการบันทึกข้อมูลภาพ Base64 (FEATURE 4)
                # หมายเหตุ: ต้องไปแก้ database.py และ schemas.py ให้มี field นี้ก่อน
                image_base64=pv_data.image_base64 
            )
            db.add(db_item)
            message = "Parking violation data received."

        elif data.table_occupancy:
            db_item = database.DBTableOccupancy(**data.table_occupancy.model_dump())
            db.add(db_item)
            message = "Table occupancy data received."

        elif data.chilled_basket_alert:
            db_item = database.DBChilledBasketAlert(**data.chilled_basket_alert.model_dump())
            db.add(db_item)
            message = "Chilled basket alert data received."

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid analytics data provided."
            )

        db.commit()
        db.refresh(db_item) 
        logger.info(f"Successfully processed analytics data. ID: {db_item.id}, Message: {message}")
        return {"message": message, "id": db_item.id}

    except Exception as e:
        db.rollback() 
        logger.exception(f"Error processing analytics data:") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inference result: {e}"
        )

# --- Get Parking Violations Endpoint (โค้ดเดิม) ---
@app.get("/DBParkingViolation/", response_model=List[schemas.ParkingViolationData], summary="Get Parking Violations")
def get_DBParkingViolation(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[str] = None,
    camera_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(database.DBParkingViolation).filter( 
        database.DBParkingViolation.event_type != "hourly_summary" 
    )
    if branch_id:
        query = query.filter(database.DBParkingViolation.branch_id == branch_id)
    if camera_id: 
        query = query.filter(database.DBParkingViolation.camera_id == camera_id)

    violations = query.order_by(database.DBParkingViolation.timestamp.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(violations)} parking violations.")
    
    # ### แก้ไข ###: ปรับปรุงการแปลงเวลาให้ถูกต้องตามชนิดข้อมูลใน DB (naive UTC)
    return [
        schemas.ParkingViolationData(
            timestamp=v.timestamp.replace(tzinfo=pytz.utc).astimezone(thailand_tz) if v.timestamp else None,
            branch=v.branch,
            branch_id=v.branch_id,
            camera_id=v.camera_id,
            event_type=v.event_type,
            car_id=v.car_id,
            current_park=v.current_park, 
            entry_time=v.entry_time.replace(tzinfo=pytz.utc).astimezone(thailand_tz) if v.entry_time else None, 
            exit_time=v.exit_time.replace(tzinfo=pytz.utc).astimezone(thailand_tz) if v.exit_time else None, 
            duration_minutes=v.duration_minutes,
            is_violation=v.is_violation,
            total_parking_sessions=v.total_parking_sessions,
            image_base64=v.image_base64 # ### เพิ่ม ###: ส่งข้อมูลภาพกลับไปด้วย
        ) for v in violations
    ]

# --- Get Table Occupancy Events Endpoint (โค้ดเดิม) ---
@app.get("/table_occupancy/", response_model=List[schemas.TableOccupancyData], summary="Get Table Occupancy Events")
def get_table_occupancy(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[str] = None,
    camera_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of recorded table occupancy events from the database.
    Can filter by branch_id and camera_id.
    """
    query = db.query(database.DBTableOccupancy)
    if branch_id:
        query = query.filter(database.DBTableOccupancy.branch_id == branch_id)
    if camera_id: 
        query = query.filter(database.DBTableOccupancy.camera_id == camera_id)
            
    occupancy_events = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(occupancy_events)} table occupancy events.")
    return occupancy_events
    pass
# --- Get Chilled Basket Alerts Endpoint (โค้ดเดิม) ---
@app.get("/chilled_basket_alerts/", response_model=List[schemas.ChilledBasketAlertData], summary="Get All Chilled Basket Alerts")
def get_chilled_basket_alerts(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[str] = None,
    camera_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of recorded chilled basket alert events from the database.
    Can filter by branch_id and camera_id.
    """
    query = db.query(database.DBChilledBasketAlert)
    if branch_id:
        query = query.filter(database.DBChilledBasketAlert.branch_id == branch_id)
    if camera_id: 
        query = query.filter(database.DBChilledBasketAlert.camera_id == camera_id)
            
    alerts = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(alerts)} chilled basket alerts.")
    return alerts
    pass
