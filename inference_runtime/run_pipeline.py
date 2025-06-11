import time
import requests
import json
import os
import sys

PATH_TO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PATH_TO_PROJECT_ROOT)

from inference_runtime.inference_wrapper.mock_ai_inference import generate_mock_inference_data

BACKEND_API_URL = "http://127.0.0.1:8000/inference_results/"

def run_infernece_pipline(camera_id: str, interval_seconds: int= 5):
    #Simulates an AI inference pipeline for a single camera, generating mock data and sending it to the FastAPI backend.
    print(f"--- Starting inference pipline for Camera: {camera_id} ---")

    while True:
        try:
            # Simulate AI Inference
            inference_data= generate_mock_inference_data(camera_id)
            json_payload= inference_data.model_dump_json() #convert to json
            print(f"[{camera_id}] Sending data: {json_payload[:100]}...")

            # Send data to FastAPI Backend
            headers= {"Content-Type": "application/json"}
            response= requests.post(BACKEND_API_URL, data= json_payload, headers=headers)

            # Process Backend Response
            if response.status_code == 201:
                print(f"[{camera_id}] Data sent successfully! Response: {response.json()}")
            else: 
                print(f"[{camera_id}] Failed to sent data. Status: {response.status_code}, Response: {response.text}")

        except requests.exceptions.ConnectionError as e:
            print(f"[{camera_id}] Connection Error: Could not connect tp FastAPI backend at {BACKEND_API_URL}."
                  "Please ensure the backend is running. Retrying in {interval_seconds} seconds...")
            
        except json.JSONDecodeError as e:
            print(f"[{camera_id}] JSON Decode Error: {e}. Response text: {response.text}")

        except Exception as e:
            print(f"[{camera_id}] An unexpected error occurred: {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    # run หลายกล้อง threading หรือ multiprocessing ตอนนี้ใช้แบบกล้องเดียวไปก่อน
    print("Starting AI CCTV Prototype Inference Runtime...")
    print("Make sure your FastAPI backend is running at https://127.0.0.1:8000")
    print("\nPress Ctrl+C to stop the pipeline.")

    import threading
    import random
    
    camera_ids = ["CAM_LOBBY_01", "CAM_EXIT_DOOR", "CAM_WEREHOUSE_03"]
    threads= []

    for cam_id in camera_ids:
        thread= threading.Thread(target= run_infernece_pipline, args=(cam_id, random.randint(3, 7)))
        threads.append(thread)
        thread.start()

    for thead in threads:
        thread.join()
