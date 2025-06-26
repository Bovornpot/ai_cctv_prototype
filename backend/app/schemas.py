from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# --- Base Schema for all Analytics Events ---
class BaseAnalyticsEvents(BaseModel):
    timestamp: datetime = Field(..., examples="2024-07-01T10:30:00Z")
    branch_id: str = Field(..., examples="15517")
    camera_id: str =Field(..., examples="cam_01")
    event_type: str = Field(...,description= "Type of event (e.g., 'parking_violation', 'table_occupancy', 'chilled_basket_alert', 'beverage_stock_update')")

class ParkingViolationData(BaseAnalyticsEvents):
    event_type: Literal["parking_violation"] = "parking_violation"
    vehicle_id: str = Field(...,examples="ABC-1234")
    # total_vechicle: int = Field(...,examples=5)
    # parking_slot_id: str = Field(...,example="P01")
    entry_time: datetime= Field(...,examples="2024-07-01T10:00:00Z")
    exit_time: Optional[datetime]= Field(None,examples="2024-07-01T10:00:00Z")
    duration_minutes: float= Field(...,examples=20.5)
    is_violation: bool= Field(...,examples=True)
    violation_reason: Optional[str] = Field(None, example="parked_over_limit")
class TableOccupancyData(BaseAnalyticsEvents):
    event_type: Literal["table_occupancy"] = "table_occupancy"
    table_id: str = Field(...,examples="T03")
    # total_table: int = Field(...,examples=5)
    is_occupied: bool =Field(...,examples=True)
    occupancy_start_time: Optional[datetime] =Field(None,examples="2024-07-01T10:00:00Z")
    occupancy_end_time: Optional[datetime]= Field(None,examples="2024-07-01T10:00:00Z")
    duration_minutes: Optional[float]= Field(None,examples="45.0")
    current_occupant_count: Optional[int]= Field(None, examples=2)

class ChilledBasketAlertData(BaseAnalyticsEvents):
    event_type: Literal["chilled_basket_alert"] = "chilled_basket_alert"
    basket_id: str= Field(...,examples="B01")
    zone_id: str = Field(...,examples="Section_A")
    entry_time: datetime= Field(...,examples="2024-07-01T10:00:00Z")
    exit_time: Optional[datetime]= Field(None,examples="2024-07-01T10:00:00Z")
    duration_minutes: float= Field(...,examples="22.0")
    is_alert_triggered: bool = Field(..., example=True)
    alert_reason: Optional[str] = Field(None, example="time_limit_exceeded")

# --- Unified Schema for incoming POST data ---
class AnalyticsDataIn(BaseModel):
    parking_violation: Optional[ParkingViolationData]= None
    table_occupancy: Optional[TableOccupancyData]= None
    chilled_basket_alert: Optional[ChilledBasketAlertData]= None

class InferenceResultResponse(BaseModel):
    message: str = Field(..., examples="Parking violation data received.")
    id: int = Field(..., examples=123)



























# #the bounding box coordinates of a detected object.
# class BoundingBox(BaseModel): 
#     y_min: int
#     x_max: int
#     y_min: int
#     y_max: int
#     confidence: Optional[float] = None

# #details of a single person detected by the AI.
# class PersonDetection(BaseModel): 
#     person_id: str
#     bbox: BoundingBox
#     age: Optional[int] = None
#     gender: Optional[str] = None
#     # add more fill form AI Predict

# #the complete AI inference result This is the main data structure that the AI pipeline will send to the Backend.
# class InferenceResult(BaseModel): 
#     timestamp: str
#     camera_id: str
#     total_people: int
#     detections: List[PersonDetection]
#     # may add other metrics form AI 
#     additional_info: Optional[Dict] = None
