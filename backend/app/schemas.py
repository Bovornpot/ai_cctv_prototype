from pydantic import BaseModel
from typing import List, Optional, Dict

#the bounding box coordinates of a detected object.
class BoundingBox(BaseModel): 
    y_min: int
    x_max: int
    y_max: int
    confidence: Optional[float] = None

#details of a single person detected by the AI.
class PersonDetection(BaseModel): 
    person_id: str
    bbox: BoundingBox
    age: Optional[int] = None
    gender: Optional[str] = None
    # add more fill form AI Predict

#the complete AI inference result This is the main data structure that the AI pipeline will send to the Backend.
class InferenceResult(BaseModel): 
    timestamp: str
    camera_id: str
    total_people: int
    detections: List[PersonDetection]
    # may add other metrics form AI 
    additional_info: Optional[Dict] = None
