import requests
import time
import random
import json
import os
import sys
import base64
from datetime import datetime, timedelta

# --- การตั้งค่าพื้นฐาน ---
API_URL = "http://127.0.0.1:8000/analytics/"
# !!! ATTENTION: Please replace "YOUR_API_KEY_HERE" with your actual API key.
API_KEY = "nemo1234" 
SIMULATION_INTERVAL_SECONDS = 1 # หน่วงเวลา 1 วินาทีในแต่ละรอบ

# --- เพิ่ม Path ไปยังโปรเจกต์หลักเพื่อ import schemas ---
try:
    PATH_TO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if PATH_TO_PROJECT_ROOT not in sys.path:
        sys.path.append(PATH_TO_PROJECT_ROOT)
    from backend.app.schemas import (
        ParkingViolationData, TableOccupancyData, ChilledBasketAlertData, AnalyticsDataIn
    )
    print("Successfully imported schemas from backend.")
except ImportError:
    print("Error: Could not import schemas from 'backend.app.schemas'.")
    print("Please ensure this script is placed in the 'inference_runtime' directory and run from there.")
    sys.exit(1)

# --- NEW: เพิ่ม Dictionary สำหรับชื่อสาขา ---
BRANCH_NAMES = {
    "1955": "สาขาลาดพร้าว",
    "15144": "สาขารัชดา",
    "10333": "สาขาสุขุมวิท",
    "2247": "สาขาสีลม",
    "22853": "สาขาบางนา",
    "12190": "สาขาพระราม 9",
    "2172": "สาขาแจ้งวัฒนะ"
}

# --- ฟังก์ชันสร้างข้อมูลจำลอง (Mock Data Generator) ---
def generate_fake_base64_image():
    """สร้างข้อมูลรูปภาพ Base64 จำลอง"""
    text_to_encode = "fake_image_data_placeholder"
    encoded_data = base64.b64encode(text_to_encode.encode('utf-8'))
    return f"data:image/jpeg;base64,{encoded_data.decode('utf-8')}"

def generate_mock_ai_results(branch_id: str, camera_id: str):
    """จำลองผลลัพธ์จาก AI (เฉพาะ ParkingViolationData)"""
    current_time = datetime.utcnow()
    results = []
    # สร้าง event 1-2 ครั้งต่อรอบเสมอ
    num_events = random.randint(1, 2)
    
    # ดึงชื่อสาขาจาก Dictionary
    branch_name = BRANCH_NAMES.get(branch_id, "สาขาไม่ระบุ")

    for _ in range(num_events):
        # --- สร้างข้อมูลเฉพาะ ParkingViolationData ---
        moment_time_minutes = random.randint(5, 300)
        entry = current_time - timedelta(minutes=moment_time_minutes)
        duration = round((current_time - entry).total_seconds() / 60, 2)
        is_violation = duration > 240
        exit_time = None if is_violation and random.random() < 0.8 else current_time
        
        # NOTE: This assumes you have added `branch: Optional[str] = None` to your ParkingViolationData schema.
        parking_data = ParkingViolationData(
            timestamp=current_time,
            branch_id=branch_id,
            branch=branch_name, # <-- FIX: เพิ่มชื่อสาขาที่นี่
            camera_id=camera_id,
            event_type="parking_violation",
            car_id=random.randint(1000, 9999),
            current_park=random.randint(20, 100),
            entry_time=entry,
            exit_time=exit_time,
            duration_minutes=duration,
            is_violation=is_violation,
            total_parking_sessions=random.randint(300, 500),
            image_base64=generate_fake_base64_image() if is_violation else None
        )
        unified_payload = AnalyticsDataIn(parking_violation=parking_data)
        results.append(unified_payload.model_dump_json())

    return results

# --- ฟังก์ชันหลักในการส่งข้อมูลและดีบัก ---
def send_data_to_api(payload: str, branch_id: str, camera_id: str):
    """ส่งข้อมูลไปยัง API และพิมพ์ผลลัพธ์การดีบักออกมา"""
    log_prefix = f"[{datetime.now():%Y-%m-%d %H:%M:%S}]"
    print(f"{log_prefix} Sending data for Branch ID: {branch_id}, Camera ID: {camera_id}...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    try:
        response = requests.post(API_URL, data=payload, headers=headers)
        response.raise_for_status()
        print(f"{log_prefix} \033[92mSuccessfully sent data. Response: {response.json()}\033[0m")
    except requests.exceptions.HTTPError as e:
        # --- จุดสำคัญในการดีบัก ---
        print(f"{log_prefix} \033[91mError sending data for Branch ID: {branch_id}, Camera ID: {camera_id}: {e}\033[0m")
        print("\n" + "="*20 + " DEBUG INFO " + "="*20)
        try:
            # พยายามพิมพ์ JSON response ที่มีรายละเอียดของ error
            print("\033[93m--- DETAIL ---\033[0m")
            print(json.dumps(e.response.json(), indent=2))
        except json.JSONDecodeError:
            # หาก response ไม่ใช่ JSON
            print("\033[93m--- RAW RESPONSE ---\033[0m")
            print(e.response.text)
        
        # พิมพ์ Payload ที่ทำให้เกิดปัญหา
        print("\033[93m--- PAYLOAD SENT ---\033[0m")
        print(json.dumps(json.loads(payload), indent=2))
        print("="*54 + "\n")
        # --- สิ้นสุดการดีบัก ---
    except requests.exceptions.RequestException as e:
        print(f"{log_prefix} \033[91mConnection Error for Branch ID: {branch_id}, Camera ID: {camera_id}: {e}\033[0m")


def main():
    """ฟังก์ชันหลักในการจำลองการทำงานของ Pipeline"""
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\033[91mError: Please set your API_KEY in the script before running.\033[0m")
        sys.exit(1)

    print("Starting AI inference pipeline simulation for debugging...")
    
    # รายชื่อสาขาจำลอง
    branch_ids = ["1955", "15144", "10333", "2247", "22853", "12190", "2172"]

    try:
        while True:
            for branch_id in branch_ids:
                num_cameras = random.randint(2, 5) # ลดจำนวนกล้องลงเพื่อให้อ่านง่ายขึ้น
                log_prefix = f"[{datetime.now():%Y-%m-%d %H:%M:%S}]"
                print(f"{log_prefix} Simulating {num_cameras} cameras for Branch ID: {branch_id}")
                
                for i in range(1, num_cameras + 1):
                    camera_id = f"{branch_id}_Cam_{i}"
                    print(f"{log_prefix} Running mock inference for Branch ID: {branch_id}, Camera ID: {camera_id}...")
                    
                    mock_results = generate_mock_ai_results(branch_id, camera_id)
                    
                    if not mock_results:
                        # ส่วนนี้จะไม่ทำงานแล้วเพราะเราสร้าง event อย่างน้อย 1 ครั้งเสมอ
                        print(f"{log_prefix} No mock data generated for Branch ID: {branch_id}, Camera ID: {camera_id} in this cycle.")
                        continue

                    for payload in mock_results:
                        send_data_to_api(payload, branch_id, camera_id)
                
                print("-" * 30)

            print(f"\n>>> Cycle complete. Waiting for {SIMULATION_INTERVAL_SECONDS} seconds... <<<\n")
            time.sleep(SIMULATION_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
