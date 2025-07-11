# main.py
from contextlib import asynccontextmanager
from typing import List, Optional, Dict 
from datetime import datetime, timedelta, time 
from sqlalchemy import func
import logging
import asyncio 

from fastapi import FastAPI, Depends, HTTPException, status, Query 
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func # Import func for aggregate functions

import schemas
import database

# Configure logging for more detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

last_hourly_summary_check_time: Optional[datetime] = None 

# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing database tables and other services...")
    database.create_db_tables()
    logger.info("Database tables ensured and ready.")
    
    asyncio.create_task(hourly_summary_task())
    logger.info("Hourly summary background task started.")

    yield 
    
    logger.info("Application shutdown: Stopping services and cleaning up...")
    logger.info("Application shutdown complete.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI CCTV Prototype Backend API",
    description="API for receiving and serving AI inference results from CCTV streams.",
    version="0.1.0",
    lifespan=lifespan 
)

# --- CORS Middleware ---
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Dependency ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Root Endpoint ---
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

# --- Health Check Endpoint ---
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Endpoint for checking API status."""
    return {"status": "ok", "message": "API is healthy and operational!"}

# --- Analytics Data Ingestion Endpoint ---
@app.post("/analytics", status_code=status.HTTP_201_CREATED,
    response_model=schemas.InferenceResultResponse,
    summary="Receive Analytics Data (Parking Violation, Table Occupancy, Chilled Basket Alert)"
)
async def create_inference_result(
    data: schemas.AnalyticsDataIn,
    db: Session = Depends(get_db)
):
    """
    Receives various types of analytics data (parking violation, table occupancy, chilled basket alerts)
    and stores them in the database.
    """
    logger.info(f"Received analytics data for processing.") 
    
    try:
        db_item = None
        message = "No valid analytics data provided."
        
        if data.parking_violation:
            pv_data = data.parking_violation
            
            db_item = database.ParkingViolation( # Using database.ParkingViolation
                timestamp=pv_data.timestamp,
                branch_id=pv_data.branch_id,
                camera_id=pv_data.camera_id,
                event_type="parking_violation", 
                car_id=pv_data.car_id,
                current_park=pv_data.current_park, # Keep this name
                entry_time=pv_data.entry_time,
                exit_time=pv_data.exit_time,
                duration_minutes=pv_data.duration_minutes,
                is_violation=pv_data.is_violation,
                total_parking_sessions=pv_data.total_parking_sessions, # Changed to total_parking_sessions
                total_parking_sessions_hourly=None # This field is only for hourly summary records
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

# --- Background task for Hourly Summary ---
async def hourly_summary_task():
    global last_hourly_summary_check_time
    logger.info("Hourly summary background task starting up.")

    while True:
        now = datetime.now()
        should_record_summary = False
        
        if last_hourly_summary_check_time is None:
            # On first startup: Set last_hourly_summary_check_time to the start of the previous full hour
            last_hourly_summary_check_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            logger.info(f"Initial last_hourly_summary_check_time set to: {last_hourly_summary_check_time}")
            # Ensure it records for the past hour if now is already past the initial check time
            if now.replace(minute=0, second=0, microsecond=0) > last_hourly_summary_check_time:
                should_record_summary = True


        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        # Check if the current hour is strictly greater than the hour of the last summary check
        if current_hour_start > last_hourly_summary_check_time.replace(minute=0, second=0, microsecond=0):
            should_record_summary = True
            logger.info(f"Hourly summary check: New hour detected. Current: {now}, Last checked: {last_hourly_summary_check_time}. Triggering summary.")


        if should_record_summary:
            summary_target_hour_start = current_hour_start - timedelta(hours=1)
            summary_target_hour_end = summary_target_hour_start + timedelta(hours=1) - timedelta(microseconds=1)

            logger.info(f"Preparing to summarize data for hour: {summary_target_hour_start.strftime('%Y-%m-%d %H:%M:%S')}")

            db_session = next(get_db())
            try:
                # Get the latest total_parking_sessions for each camera within the hour
                # We need to find the MAX(total_parking_sessions) for each camera for that hour.
                # This assumes total_parking_sessions is monotonically increasing.
                
                # Subquery to find the latest timestamp for each camera within the hour
                subquery = db_session.query(
                    database.DBParkingViolation.camera_id, # <<< แก้ไขตรงนี้
                    func.max(database.DBParkingViolation.timestamp).label("max_timestamp") # <<< แก้ไขตรงนี้
                ).filter(
                    database.DBParkingViolation.event_type == "parking_violation", # <<< แก้ไขตรงนี้
                    database.DBParkingViolation.timestamp >= summary_target_hour_start, # <<< แก้ไขตรงนี้
                    database.DBParkingViolation.timestamp <= summary_target_hour_end # <<< แก้ไขตรงนี้
                ).group_by(database.DBParkingViolation.camera_id).subquery() # <<< แก้ไขตรงนี้

                # Join with the subquery to get the actual records corresponding to the latest timestamps
                latest_events_in_hour = db_session.query(database.DBParkingViolation).join( # <<< แก้ไขตรงนี้
                    subquery,
                    (database.DBParkingViolation.camera_id == subquery.c.camera_id) & # <<< แก้ไขตรงนี้
                    (database.DBParkingViolation.timestamp == subquery.c.max_timestamp) # <<< แก้ไขตรงนี้
                ).filter(
                     database.DBParkingViolation.event_type == "parking_violation" # <<< แก้ไขตรงนี้
                ).all()

                for event in latest_events_in_hour:
                    total_sessions_for_hour += (event.total_parking_sessions or 0) 
             
                new_sessions_in_hour = 0
                unique_camera_ids = db_session.query(database.DBParkingViolation.camera_id).filter( # <<< แก้ไขตรงนี้
                    database.DBParkingViolation.event_type == "parking_violation", # <<< แก้ไขตรงนี้
                    database.DBParkingViolation.timestamp >= summary_target_hour_start, # <<< แก้ไขตรงนี้
                    database.DBParkingViolation.timestamp <= summary_target_hour_end # <<< แก้ไขตรงนี้
                ).distinct().all()

                for cam_id_tuple in unique_camera_ids:
                    cam_id = cam_id_tuple[0]
                    
                    # Get the total_parking_sessions at the start of the hour for this camera
                    start_of_hour_event = db_session.query(database.DBParkingViolation.total_parking_sessions)\
                        .filter(
                            database.DBParkingViolation.event_type == "parking_violation", # <<< แก้ไขตรงนี้
                            database.DBParkingViolation.camera_id == cam_id, # <<< แก้ไขตรงนี้
                            database.DBParkingViolation.timestamp >= summary_target_hour_start # <<< แก้ไขตรงนี้
                        ).order_by(database.DBParkingViolation.timestamp.asc()).first()
                    
                    start_value = start_of_hour_event[0] if start_of_hour_event and start_of_hour_event[0] is not None else 0

                    # Get the total_parking_sessions at the end of the hour for this camera
                    end_of_hour_event = db_session.query(database.DBParkingViolation.total_parking_sessions)\
                        .filter(
                            database.DBParkingViolation.event_type == "parking_violation", # <<< แก้ไขตรงนี้
                            database.DBParkingViolation.camera_id == cam_id, # <<< แก้ไขตรงนี้
                            database.DBParkingViolation.timestamp <= summary_target_hour_end # <<< แก้ไขตรงนี้
                        ).order_by(database.DBParkingViolation.timestamp.desc()).first()
                        
                    end_value = end_of_hour_event[0] if end_of_hour_event and end_of_hour_event[0] is not None else 0

                    if end_value >= start_value:
                        new_sessions_in_hour += (end_value - start_value)
                    else:
                        # This case indicates a counter reset or unexpected behavior.
                        # For now, just add the end_value as if it's the total sessions for this segment.
                        logger.warning(f"Counter reset detected for camera {cam_id} from {summary_target_hour_start.strftime('%H:%M')} to {summary_target_hour_end.strftime('%H:%M')}. End value: {end_value}")
                        new_sessions_in_hour += end_value # Add the total sessions observed at the end of the period
                
                db_summary = database.DBParkingViolation( # <<< แก้ไขตรงนี้
                    timestamp=summary_target_hour_start, 
                    branch_id="AGGREGATED_BRANCH", 
                    camera_id="AGGREGATED_CAMERAS", 
                    event_type="hourly_summary", 
                    car_id=None, 
                    current_park=None, 
                    entry_time=None,
                    exit_time=None,
                    duration_minutes=None,
                    is_violation=None,
                    total_parking_sessions=None, # This record is not about a specific current state
                    total_parking_sessions_hourly=new_sessions_in_hour # Using the newly calculated sessions for the hour
                )
                
                db_session.add(db_summary)
                db_session.commit()
                db_session.refresh(db_summary)
                
                logger.info(f"Hourly summary recorded for {summary_target_hour_start.strftime('%Y-%m-%d %H:%M')}: {new_sessions_in_hour} total sessions.")
                
            except Exception as e:
                db_session.rollback() 
                logger.error(f"Error recording hourly summary for {summary_target_hour_start}: {e}", exc_info=True)
            finally:
                db_session.close()

            last_hourly_summary_check_time = summary_target_hour_start 
            
        seconds_to_sleep = 60 - (now.second + now.microsecond / 1_000_000) % 60 + 0.1
        logger.debug(f"Sleeping for {seconds_to_sleep:.2f} seconds.")
        await asyncio.sleep(seconds_to_sleep)

# --- Get Parking Violations Endpoint ---
@app.get("/DBParkingViolation/", response_model=List[schemas.ParkingViolationData], summary="Get Parking Violations")
def get_DBParkingViolation(
    skip: int = 0,
    limit: int = 100,
    branch_id: Optional[str] = None,
    camera_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of recorded parking violation events from the database.
    Can filter by branch_id and camera_id.
    """
    query = db.query(database.ParkingViolation).filter(
        database.ParkingViolation.event_type == "parking_violation" 
    )
    if branch_id:
        query = query.filter(database.ParkingViolation.branch_id == branch_id)
    if camera_id: 
        query = query.filter(database.ParkingViolation.camera_id == camera_id)

    violations = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(violations)} parking violations.")
    return [
        schemas.ParkingViolationData(
            timestamp=v.timestamp,
            branch_id=v.branch_id,
            camera_id=v.camera_id,
            event_type=v.event_type,
            car_id=v.car_id,
            current_park=v.current_park, # Keep this name
            entry_time=v.entry_time,
            exit_time=v.exit_time,
            duration_minutes=v.duration_minutes,
            is_violation=v.is_violation,
            total_parking_sessions=v.total_parking_sessions # Changed to total_parking_sessions
        ) for v in violations
    ]

# --- Get Table Occupancy Events Endpoint ---
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

# --- Get Chilled Basket Alerts Endpoint ---
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

# --- New Endpoint for Hourly Parking Summary (From DB) ---
@app.get("/hourly_parking_summary/", response_model=List[schemas.ParkingViolationData], summary="Get Hourly Parking Summaries")
def get_hourly_parking_summary(
    start_time: Optional[datetime] = Query(None, description="Start datetime for summary (e.g., 2024-07-01T00:00:00)"),
    end_time: Optional[datetime] = Query(None, description="End datetime for summary (e.g., 2024-07-02T23:59:59)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves hourly parking summary records from the database.
    Can filter by a time range.
    """
    query = db.query(database.ParkingViolation).filter(
        database.ParkingViolation.event_type == "hourly_summary"
    )
    
    if start_time:
        query = query.filter(database.ParkingViolation.timestamp >= start_time)
    if end_time:
        query = query.filter(database.ParkingViolation.timestamp <= end_time)
        
    query = query.order_by(database.ParkingViolation.timestamp.asc()) 
    
    summaries = query.all()
    logger.info(f"Retrieved {len(summaries)} hourly parking summaries.")
    
    return [
        schemas.ParkingViolationData(
            timestamp=s.timestamp,
            branch_id=s.branch_id,
            camera_id=s.camera_id,
            event_type=s.event_type,
            car_id=None, 
            current_park=0, 
            entry_time=s.timestamp, # Use summary timestamp
            exit_time=None,
            duration_minutes=0.0, 
            is_violation=False, 
            total_parking_sessions=s.total_parking_sessions_hourly or 0 # Map hourly summary value to total_parking_sessions in schema
        ) for s in summaries
    ]
