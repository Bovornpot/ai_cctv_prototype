import random
import json
import os
import sys
import base64
from datetime import datetime, timedelta
from backend.app.schemas import (
    ParkingViolationData, TableOccupancyData, ChilledBasketAlertData, AnalyticsDataIn)

PATH_TO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PATH_TO_PROJECT_ROOT)

def generate_fake_base64_image():
    """Generates a simple placeholder base64 string."""
    text_to_encode = "fake_image_data_placeholder"
    encoded_data = base64.b64encode(text_to_encode.encode('utf-8'))
    return f"data:image/jpeg;base64,{encoded_data.decode('utf-8')}"

def generate_mock_ai_results(branch_id: str, camera_id: str):
    """จำลองผลลัพธ์จาก AI ให้สอดคล้องกับ Pydantic Schemas"""
    current_time = datetime.utcnow()
    results = []
    num_events = random.randint(1, 3) # Ensure at least one event is generated

    for _ in range(num_events):
        event_type = random.choice([
            "parking_violation",
            "table_occupancy",
            "chilled_basket_alert"
        ])

        # Mock Parking Violation Data
        if event_type == "parking_violation":
            moment_time_minutes = random.randint(5, 300) # Increased range for more violations
            entry = current_time - timedelta(minutes=moment_time_minutes)
            duration = round((current_time - entry).total_seconds() / 60, 2)
            is_violation = duration > 240 # Violation if over 4 hours
            exit_time = None if is_violation and random.random() < 0.8 else current_time

            # FIX: Corrected fields to match ParkingViolationData schema
            parking_data = ParkingViolationData(
                timestamp=current_time,
                branch_id=branch_id,
                camera_id=camera_id,
                event_type="parking_violation",
                car_id=random.randint(1000, 9999), # CHANGED: from vehicle_id to car_id (int)
                current_park=random.randint(20, 100), # CHANGED: from total_vehicle to current_park
                entry_time=entry,
                exit_time=exit_time,
                duration_minutes=duration,
                is_violation=is_violation,
                total_parking_sessions=random.randint(300, 500), # ADDED: missing required field
                image_base64=generate_fake_base64_image() if is_violation else None # ADDED: for completeness
            )
            unified_payload = AnalyticsDataIn(parking_violation=parking_data)

        # Mock Table Occupancy Data
        elif event_type == "table_occupancy":
            table_id = f"T{random.randint(1, 10)}"
            is_occupied = random.choice([True, False])
            
            # REVISED: Simplified and more logical data generation
            if is_occupied:
                # Table is currently occupied
                start_time = current_time - timedelta(minutes=random.randint(5, 60))
                table_data = TableOccupancyData(
                    timestamp=current_time,
                    branch_id=branch_id,
                    camera_id=camera_id,
                    table_id=table_id,
                    is_occupied=True,
                    occupancy_start_time=start_time,
                    occupancy_end_time=None,
                    duration_minutes=round((current_time - start_time).total_seconds() / 60, 2),
                    current_occupant_count=random.randint(1, 4)
                )
            else:
                # Table just became vacant
                start_time = current_time - timedelta(minutes=random.randint(5, 120))
                end_time = current_time
                table_data = TableOccupancyData(
                    timestamp=current_time,
                    branch_id=branch_id,
                    camera_id=camera_id,
                    table_id=table_id,
                    is_occupied=False,
                    occupancy_start_time=start_time,
                    occupancy_end_time=end_time,
                    duration_minutes=round((end_time - start_time).total_seconds() / 60, 2),
                    current_occupant_count=0
                )
            unified_payload = AnalyticsDataIn(table_occupancy=table_data)

        # Mock Chilled Basket Alert Data
        elif event_type == "chilled_basket_alert":
            moment_time_minutes = random.randint(1, 60)
            entry = current_time - timedelta(minutes=moment_time_minutes)
            duration = round((current_time - entry).total_seconds() / 60, 2)
            is_alert_triggered = duration > 15 # Alert if over 15 minutes
            
            exit_time = None
            if not is_alert_triggered:
                 exit_time = current_time
            elif random.random() < 0.3: # 30% chance the alert is resolved
                 exit_time = current_time

            chilled_data = ChilledBasketAlertData(
                timestamp=current_time,
                branch_id=branch_id,
                camera_id=camera_id,
                basket_id=f"B{random.randint(1, 30)}",
                zone_id="Section_A",
                entry_time=entry,
                exit_time=exit_time,
                duration_minutes=duration,
                is_alert_triggered=is_alert_triggered,
                alert_reason="time_limit_exceeded" if is_alert_triggered else None
            )
            unified_payload = AnalyticsDataIn(chilled_basket_alert=chilled_data)

        results.append(unified_payload.model_dump_json())

    return results

if __name__ == '__main__':
    # Example of how to run this script
    mock_results = generate_mock_ai_results(branch_id="15517", camera_id="cam_01")
    print(f"Generated {len(mock_results)} mock event(s):")
    for result_json in mock_results:
        # Pretty print the JSON
        parsed_json = json.loads(result_json)
        print(json.dumps(parsed_json, indent=2))

