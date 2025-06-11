import random
import time
from datetime import datetime, timezone
from typing import Dict, Any
import uuid
import json

def generate_mock_inference_data(camera_id: str) -> Dict[str, Any]: #จองลองผลลัพธ์จาก AI
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds') + "Z"
    total_people = random.randint(0,10)
    detections = []

    for _ in range(total_people): # random data for each total_people
        x_min = random.randint(0,1920 - 100)
        y_min = random.randint(0, 1080 - 100)
        x_max = x_min + random.randint(50,100)
        y_max = y_min + random.randint(50,100)
        confidence = round(random.uniform(0.7, 0.99), 2)
        age = random.randint(18, 60) if random.random() > 0.3 else None
        gender = random.choice(['male','female']) if random.random() > 0.2 else None

    detections.append({ #add random data to detections that have the same structure from PersonDetection(schemas.py)
        "person_id": str(uuid.uuid4()),
        "bbox": {
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "confidence": confidence
        },
        "age": age,
        "gender": gender
    })

    result = {
        "timestamp": timestamp,
        "camera_id": camera_id,
        "total_people": total_people,
        "detections": detections,
        "additional_info": {
            "mock_data_source": "mock_ai_inference.py",
            "processing_time_ms": random.randint(10,100)
        }
    }
    return result

if __name__ == "__main__": #only run form Terminal
    print("--- Generating Mock AI Inference Data ---")
    mock_data = generate_mock_inference_data(camera_id = "CAM_LOBBY_01")
    print(json.dumps(mock_data, indent=2))

    print("\n--- Another Mock Data ---")
    mock_data_2 =   generate_mock_inference_data(camera_id = "CAM_EXIT_DOOR")
    print(json.dumps(mock_data_2, indent=2))