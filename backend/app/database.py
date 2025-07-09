from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./data/db.sqlite" #Path batabase data folder

engine= create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBParkingViolation(Base):
    __tablename__= "parking_violations"
    id= Column(Integer, primary_key=True, index=True)
    timestamp= Column(DateTime, index=True, default=datetime.utcnow)
    branch_id = Column(String, index=True)
    camera_id= Column(String, index=True)
    event_type = Column(String)
    vehicle_id= Column(String, index=True)
    total_vehicle= Column(Integer, index=True)
    # parking_slot_id= Column(String, index=True)
    entry_time= Column(DateTime)
    exit_time = Column(DateTime, nullable=True)
    duration_minutes= Column(Float)
    is_violation= Column(Boolean)
    violation_reason= Column(String, nullable=True)
    
class DBTableOccupancy(Base):
    __tablename__= "table_occupancy"
    id= Column(Integer, primary_key=True, index=True)
    timestamp= Column(DateTime, index=True, default=datetime.utcnow)
    branch_id = Column(String, index=True)
    camera_id= Column(String, index=True)
    event_type = Column(String)
    table_id = Column(String, index=True)
    # total_table= Column(Integer, index=True)
    is_occupied= Column(Boolean)
    occupancy_start_time= Column(DateTime, index=True)
    occupancy_end_time= Column(DateTime, nullable=True)
    duration_minutes= Column(Float, nullable=True)
    current_occupant_count= Column(Integer, nullable=True)

class DBChilledBasketAlert(Base):
    __tablename__= "chilled_basket_alerts"
    id= Column(Integer, primary_key=True, index=True)
    timestamp= Column(DateTime, index=True, default=datetime.utcnow)
    branch_id = Column(String, index=True)
    camera_id= Column(String, index=True)
    event_type = Column(String)
    basket_id= Column(String, index=True)
    zone_id= Column(String)
    entry_time= Column(DateTime, index=True)
    exit_time= Column(DateTime, nullable=True)
    duration_minutes= Column(Float, nullable=True)
    is_alert_triggered= Column(Boolean)
    alert_reason= Column(String, nullable=True)


# Function to create tables (call this once when the app starts)
def create_db_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/updated.")

# Dependency for FastAPI to get DB session
def get_db():
    db= SessionLocal()
    try: 
        yield db
    finally:
        db.close() 
 