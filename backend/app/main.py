from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schemas, database
from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO) #ดู log ที่ละเอียดขึ้น

app = FastAPI(
    title="AI CCTV Prototype Backend API",
    description="API for receiving and serving AI inference results from CCTV streams.",
    version="0.1.0"
)

app.add_middleware( 
    CORSMiddleware,
    allow_origins = ["*"], #ไว้มาแก้ไขเป็นOriginของ Frontend ตอนนี้ให้อนุญาติทั้งหมดไปก่อน
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Create database tables on startup
@app.on_event("startup") 
def on_startup(): #runs when the FastAPI application starts up.
    database.create_db_tables()
    print("Database tables ensured and ready.")

def get_db():
    db= database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(): #Root endpoint that returns a simple HTML welcome page.
    #for checking if api is running

    return """
    <html>
        <head>
            <title>AI CCTV Prototype API</title>
        </head>
        <body>
            <h1>Welcome to AI CCTV Prototype Backend API!</h1>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation (Swagger UI).</p>
            <p>Visit <a href="/redoc">/redoc</a> for alternative API documentation.</p>
        </body>
    </html>
    """

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(): #checking status endpoint
    return {"status": "ok", "message": "API is healthy and operational!"}

@app.post("/analytics",status_code = status.HTTP_201_CREATED,
    response_model=schemas.InferenceResultResponse,
    summary = "Receive Analytics Data"
)
async def create_inference_result(
    data: schemas.AnalyticsDataIn, # FastAPI จะรับ JSON Body ของ Request และ แปลงให้ตรงตามตาม schemas.py
    db: Session= Depends(get_db)
):
    try:
        db_item = None
        message = "No valid analytics data provided"

        if data.parking_violation:
            db_item= database.DBParkingViolation(**data.parking_violation.model_dump())
            db.add(db_item)
            message = "Parking violation data received."
        
        elif data.table_occupancy:
            db_item= database.DBTableOccupancy(**data.table_occupancy.model_dump())
            db.add(db_item)
            message = "Table occupancy data received."
        
        elif data.chilled_basket_alert:
            db_item= database.DBChilledBasketAlert(**data.chilled_basket_alert.model_dump())
            db.add(db_item)
            message =  "Chilled basket alert data received."
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid analytics data provided."
            )
        db.commit()
        db.refresh(db_item)
        return {"message": message, "id": db_item.id}

    except Exception as e:
        db.rollback()
        logging.exception(f"Error processing analytics data:")
        print(f"\n--- DEBUG ERROR START ---")
        print(f"Type of error: {type(e)}")
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()
        print(f"--- DEBUG ERROR END ---\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inference result: {e}"
        )
    
@app.get("/parking_violations/", response_model= list[schemas.ParkingViolationData], summary="Get Parking Violations")
def get_parking_violations(
    skip: int=0,
    limit: int =100,
    branch_id: Optional[str] = None,
    db: Session= Depends(get_db)
):
    query = db.query(database.DBParkingViolation)
    if branch_id:
            query= query.filter(database.DBParkingViolation.branch_id == branch_id)

    violations= query.offset(skip).limit(limit).all()
    return violations

@app.get("/table_occupancy/", response_model= list[schemas.TableOccupancyData], summary="Get Table Occupancy Events")
def get_table_occupancy(
    skip: int=0,
    limit: int =100,
    branch_id: Optional[str] = None,
    db: Session= Depends(get_db)
):
    query = db.query(database.DBTableOccupancy)
    if branch_id:
            query= query.filter(database.DBTableOccupancy.branch_id == branch_id)
            
    occupancy_events= query.offset(skip).limit(limit).all()
    return occupancy_events

@app.get("/chilled_basket_alerts/", response_model= list[schemas.ChilledBasketAlertData], summary="Get All Chilled Basket Alerts")
def get_chilled_basket_alerts(
    skip: int=0,
    limit: int =100,
    branch_id: Optional[str] = None,
    db: Session= Depends(get_db)
):
    query = db.query(database.DBChilledBasketAlert)
    if branch_id:
            query= query.filter(database.DBChilledBasketAlert.branch_id == branch_id)
            
    alerts= query.offset(skip).limit(limit).all()
    return alerts