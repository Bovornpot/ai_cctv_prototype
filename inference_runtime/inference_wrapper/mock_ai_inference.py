import random
import json
import os
import sys
from datetime import datetime, timedelta
from backend.app.schemas import (
    ParkingViolationData, TableOccupancyData, ChilledBasketAlertData, AnalyticsDataIn)

PATH_TO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PATH_TO_PROJECT_ROOT)

def generate_mock_ai_results(branch_id: str, camera_id: str): #จำลองผลลัพธ์จาก AI
    current_time = datetime.utcnow()
    results = []
    num_events= random.randint(0,3)

    for _ in range(num_events):
        event_type=random.choice([
            "parking_violation",
            "table_occupancy",
            "chilled_basket_alert"
        ])  

        #Mock Parking Violation Data
        if event_type == "parking_violation":
            moment_time_minutes = random.randint(5,120)
            entry= current_time - timedelta(minutes=moment_time_minutes)
            duration= round((current_time - entry).total_seconds() /60,2)
            total_vehicle=random.randint(1,10)
            is_violation= False
            violation_reason="within_time"
            exit_time= current_time

            if moment_time_minutes > 30:
                is_violation= True
                violation_reason = random.choice(["parked_over_limit", "unauthorized_parking", "blocking_access"])
                if random.random() < 0.5:
                    exit_time = None

            parking_data= ParkingViolationData(
                timestamp=current_time,
                branch_id=branch_id,
                camera_id=camera_id,
                event_type="parking_violation",
                vehicle_id=f"CAR_{random.randint(100,999)}",
                total_vehicle=total_vehicle,
                entry_time=entry,
                exit_time=exit_time,
                duration_minutes=duration,
                is_violation=is_violation,
                violation_reason=violation_reason
            )

        #Mock Table Occupancy Data
        elif event_type == "table_occupancy":
            table_id = f"T{random.randint(1, 10)}"
            is_occupied= random.choice([True,False])
            occupancy_start_time= None
            occupancy_end_time= None
            duration= None
            current_occupant_count= 0

            if is_occupied:
                duration_minutes_mock= random.randint(10,90)
                occupancy_start_time= current_time - timedelta(minutes=duration_minutes_mock)
                current_occupant_count= random.randint(1,4)
                if random.random() < 0.7:
                    occupancy_end_time = None
                    duration= round((current_time - occupancy_start_time).total_seconds() / 60,2)
                else:
                    occupancy_end_time= current_time
                    duration= round((occupancy_end_time - occupancy_start_time).total_seconds() / 60,2)

            else:
                occupancy_end_time = current_time
                if random.random() < 0.5:
                    occupancy_start_time= current_time -timedelta(minutes=random.randint(1,10))
                    duration= round((occupancy_end_time - occupancy_start_time).total_seconds() / 60,2)
                else:
                    occupancy_start_time= None
                    duration = 0

            table_data = TableOccupancyData(
                timestamp=current_time,
                branch_id= branch_id,
                camera_id=camera_id,
                event_type="table_occupancy",
                table_id=table_id,
                is_occupied=is_occupied,
                occupancy_start_time=occupancy_start_time,
                occupancy_end_time=occupancy_end_time,
                duration_minutes=duration,
                current_occupant_count=current_occupant_count
            )

        #Mock Chilled Basket Alert Data
        elif event_type == "chilled_basket_alert":
            moment_time_minutes = random.randint(1, 60)
            entry = current_time - timedelta(minutes=moment_time_minutes)
            duration = round((current_time - entry).total_seconds() / 60, 2)
            is_alert_triggered = False
            alert_reason = "within_time"
            exit_time = None

            if moment_time_minutes > 30:
                is_alert_triggered = True
                alert_reason = "time_limit_exceeded"
                if random.random() < 0.5:
                    exit_time=None
                else:
                    exit_time =current_time

            else:
                if random.random() < 0.7:
                    exit_time=current_time

            chilled_data = ChilledBasketAlertData(
                timestamp=current_time,
                branch_id = branch_id,
                camera_id=camera_id,
                event_type="chilled_basket_alert",
                basket_id=f"B{random.randint(1,30)}",
                zone_id="Section_A",
                entry_time=entry,
                exit_time=exit_time,
                duration_minutes=duration,
                is_alert_triggered=is_alert_triggered,
                alert_reason=alert_reason
            )

        unified_payload = AnalyticsDataIn(
            parking_violation=None,
            table_occupancy=None,
            chilled_basket_alert=None
        )

        if event_type == "parking_violation":
            unified_payload.parking_violation = parking_data
        elif event_type == "table_occupancy":
            unified_payload.table_occupancy = table_data
        elif event_type == "chilled_basket_alert":
            unified_payload.chilled_basket_alert = chilled_data

        results.append(unified_payload.model_dump_json())
                
    return results