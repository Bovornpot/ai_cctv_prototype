import time
import requests
import json
import os
import sys
import random
from datetime import datetime

PATH_TO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PATH_TO_PROJECT_ROOT)

from inference_wrapper.mock_ai_inference import generate_mock_ai_results

BACKEND_API_URL = "http://127.0.0.1:8000/analytics" 

NUM_MOCK_BRANCHES = 5 #จำลอง 5 สาขา
BRANCHES = [str(random.randint(100, 29999)) for _ in range(NUM_MOCK_BRANCHES)]

def send_to_backend(branch_id: str, camera_id: str, data_payload_json_string: str):
    headers= {"Content-Type": "application/json"}
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sending data for Branch ID: {branch_id}, Camera ID: {camera_id}...")

    try:
        response= requests.post(BACKEND_API_URL, data=data_payload_json_string, headers=headers, timeout = 5)
        response.raise_for_status()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully sent data for Branch ID: {branch_id}, Camera ID: {camera_id}. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Error sending data for Branch ID: {branch_id}, Camera ID: {camera_id}: {e}]")

def main():
    print("Starting AI inference pipeline simulation...")
    simulation_interval_seconds = 10

    while True:
        for branch_id in BRANCHES:
            num_cameras_for_this_branch = random.randint(8, 16)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Simulating {num_cameras_for_this_branch} cameras for Branch ID: {branch_id}")
            
            for i in range(num_cameras_for_this_branch):
                camera_id = f"{branch_id}_Cam_{i+1}"

                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running mock inference for Branch ID: {branch_id}, Camera ID: {camera_id}...")
                mock_results_json_string_list= generate_mock_ai_results(branch_id=branch_id, camera_id=camera_id)

                if mock_results_json_string_list:
                    for result_json_string in mock_results_json_string_list:
                        send_to_backend(branch_id, camera_id, result_json_string)
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No mock data generated for Branch ID: {branch_id}, Camera ID: {camera_id} in this cycle.")
        
        time.sleep(simulation_interval_seconds)

if __name__ =="__main__":
    main()



