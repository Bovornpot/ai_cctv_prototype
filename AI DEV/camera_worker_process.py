# camera_worker_process.py

# --- ส่วน Import ---
from pathlib import Path
import torch
import cv2
import time
import numpy as np
import queue
import torch.serialization
import torch.nn as nn
import requests
import json
from datetime import datetime
from typing import Optional
import logging
import asyncio
import httpx
from collections import deque 
import base64 

# Configure logging for this Worker Process
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__)

# Import specific modules from ultralytics
from ultralytics.yolo.engine.model import YOLO
from ultralytics.yolo.utils.files import increment_path
from ultralytics.yolo.utils.plotting import Annotator, colors
from ultralytics.nn.tasks import PoseModel, DetectionModel, SegmentationModel
from ultralytics.nn.modules.conv import Conv, Concat
from ultralytics.nn.modules.block import C2f, Bottleneck, SPPF, DFL
from ultralytics.nn.modules.head import Detect, Segment, Pose

# ### แก้ไข ###: Import ฟังก์ชันสำหรับหลายโซนจาก utils.py
from utils import load_parking_zone, is_point_in_any_polygon, get_bbox_center, draw_parking_zones, write_mot_results
from utils import adjust_brightness_clahe, adjust_brightness_histogram
from car_tracker_manager import CarTrackerManager

# แก้ไข UnpicklingError
torch.serialization.add_safe_globals([
    nn.Sequential, nn.Conv2d, nn.BatchNorm2d, nn.MaxPool2d, nn.AdaptiveAvgPool2d,
    nn.Linear, nn.Dropout, nn.Identity, nn.SiLU, nn.ModuleList, nn.Upsample, getattr,
    PoseModel, DetectionModel, SegmentationModel,
    Conv, Concat, C2f, Bottleneck, SPPF, DFL, Detect, Segment, Pose
])

# Optional: Disable Ultralytics default plotting
try:
    from ultralytics.yolo.utils import plotting
except AttributeError:
    logger.warning("Ultralytics plotting functions not found or already modified. Manual drawing might overlap.")

# --- ค่าคงที่และตัวแปร Global ---
FASTAPI_BACKEND_URL = "http://127.0.0.1:8000/analytics"
api_retry_queue = deque(maxlen=100)

# --- ฟังก์ชันสำหรับส่งข้อมูลไปที่ API (เวอร์ชันปรับปรุง) ---
async def send_data_to_api(camera_id: str, event_payload: dict, api_key: str):
    current_logger = logging.getLogger(f"camera_worker_process.{camera_id}")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    try:
        current_logger.info(f"[{camera_id}] Attempting to send data...")
        async with httpx.AsyncClient() as client:
            response = await client.post(FASTAPI_BACKEND_URL, json=event_payload, headers=headers, timeout=10)
            response.raise_for_status()
        current_logger.info(f"[{camera_id}] Successfully sent data.")
        return True
    except (httpx.RequestError, httpx.TimeoutException) as e:
        current_logger.warning(f"[{camera_id}] Could not send data: {e}. Adding to retry queue.")
        api_retry_queue.append({'payload': event_payload, 'api_key': api_key})
        return False
    except Exception as e:
        current_logger.exception(f"[{camera_id}] Unexpected error in send_data_to_api:")
        return False

# --- ฟังก์ชัน Worker หลัก (เวอร์ชันปรับปรุง) ---
async def camera_worker_async(cam_cfg, config, display_queue, stats_queue, show_display_flag):
    # --- ส่วนตั้งค่าเริ่มต้น ---
    cam_name = cam_cfg['name']
    source_path = str(cam_cfg['source_path'])
    roi_file = Path(cam_cfg['parking_zone_file'])
    branch_id = cam_cfg.get('branch_id', 'unknown_branch')
    camera_id = cam_cfg.get('camera_id', cam_name)
    logger = logging.getLogger(f"camera_worker_process.{camera_id}")
    logger.info(f"[{cam_name}] Worker started.")
    api_key = config.get('api_key', 'default_key_if_not_in_config')
    
    target_inference_width = config.get('performance_settings', {}).get('target_inference_width', 640)
    frames_to_skip = config.get('performance_settings', {}).get('frames_to_skip', 1)
    draw_bounding_box = config.get('performance_settings', {}).get('draw_bounding_box', True)

    device_str = config.get('device', 'cpu')
    logger.info(f"[{cam_name}] Using device: {device_str}")
    model = YOLO(config['yolo_model'])
    model.to(device_str)
    if config.get('half_precision', False) and device_str != 'cpu':
        model.half()
    model.fuse()
    model.track_config = Path(config['boxmot_config_path'])
    model.reid_weights = Path(config['reid_model'])
    class_names = model.names

    cam_save_dir = increment_path(Path(config['output_dir']) / cam_name, exist_ok=False)
    cam_save_dir.mkdir(parents=True, exist_ok=True)
    
    # ### แก้ไข ###: เปลี่ยนชื่อตัวแปรเพื่อความชัดเจน
    parking_zones_original = load_parking_zone(roi_file)
    if parking_zones_original is None or not parking_zones_original:
        logger.error(f"[{cam_name}] Error: ROI coordinates file '{roi_file}' not found or invalid. Exiting worker.")
        return

    cap = cv2.VideoCapture(source_path)
    
    original_video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if original_video_width == 0 or original_video_height == 0:
        ret, temp_frame = cap.read()
        if ret:
            original_video_height, original_video_width = temp_frame.shape[:2]
        else:
            logger.warning(f"[{cam_name}] Could not determine video dimensions.")
            original_video_width, original_video_height = target_inference_width, target_inference_width

    target_inference_height = int(original_video_height * (target_inference_width / original_video_width)) if original_video_width > 0 else 480
    scale_x = target_inference_width / original_video_width if original_video_width > 0 else 1
    scale_y = target_inference_height / original_video_height if original_video_height > 0 else 1
    
    # ### แก้ไข ###: ปรับการคำนวณ scale ให้รองรับหลายโซน
    scaled_parking_zones = []
    for polygon in parking_zones_original:
        scaled_polygon = [[int(p[0] * scale_x), int(p[1] * scale_y)] for p in polygon]
        scaled_parking_zones.append(scaled_polygon)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30.0

    parking_time_limit_minutes = cam_cfg.get('parking_time_limit_minutes', config.get('parking_time_limit_minutes', 15))
    warning_time_limit_minutes = cam_cfg.get('warning_time_limit_minutes', config.get('warning_time_limit_minutes'))
    if warning_time_limit_minutes is None:
        warning_time_limit_minutes = parking_time_limit_minutes - 2 if isinstance(parking_time_limit_minutes, int) and parking_time_limit_minutes > 2 else 13

    # ### แก้ไข ###: ส่งลิสต์ของโซนทั้งหมดเข้าไปใน CarTrackerManager
    car_tracker_manager = CarTrackerManager(
        scaled_parking_zones,
        parking_time_limit_minutes,
        cam_cfg.get('movement_threshold_px', config.get('movement_threshold_px', 5)),
        cam_cfg.get('movement_frame_window', config.get('movement_frame_window', 30)),
        warning_time_limit_minutes,
        fps,
        config
    )
    
    video_writer = None
    if config.get('save_video', False):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video_path = cam_save_dir / f"output_{Path(source_path).stem}.mp4"
        video_writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (target_inference_width, target_inference_height))
    
    mot_save_path = cam_save_dir / "mot_results" / "mot.txt" if config.get('save_mot_results', False) else None
    if mot_save_path:
        mot_save_path.parent.mkdir(parents=True, exist_ok=True)
        
    frame_idx = 0
    start_time = time.time()

    # --- ลูปหลักในการประมวลผล ---
    while True:
        ret, frame = cap.read()
        
        # ### เพิ่ม ###: ตรรกะการจัดการเมื่อวิดีโอจบ หรือกล้องหลุด
        if not ret:
            is_video_file = not source_path.startswith(('rtsp://', 'http://', 'https://')) and not source_path.isnumeric()
            
            if is_video_file:
                logger.warning(f"[{cam_name}] End of video file. Resetting tracker and looping video.")
                if hasattr(model, 'tracker'):
                    model.tracker.reset()
                car_tracker_manager.reset()
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_idx = 0
                time.sleep(1)
                continue
            else:
                logger.warning(f"[{cam_name}] Stream ended or connection lost. Attempting to reconnect...")
                cap.release()
                time.sleep(15)
                cap = cv2.VideoCapture(source_path)
                continue

        frame_idx += 1
        
        if frames_to_skip > 1 and (frame_idx % frames_to_skip != 0):
            if show_display_flag and frame is not None:
                temp_frame_for_display = cv2.resize(frame, (target_inference_width, target_inference_height))
                try:
                    display_queue.put((cam_name, temp_frame_for_display.copy()))
                except queue.Full: pass
            continue

        resized_frame = cv2.resize(frame, (target_inference_width, target_inference_height))
        
        if config.get('enable_brightness_adjustment', False):
            if config.get('brightness_method', 'clahe').lower() == 'clahe':
                resized_frame = adjust_brightness_clahe(resized_frame)
            elif config.get('brightness_method', 'clahe').lower() == 'histogram':
                resized_frame = adjust_brightness_histogram(resized_frame)

        results = model.track(resized_frame, persist=True, show=False, conf=config['detection_confidence_threshold'], classes=config['car_class_id'], verbose=False)

        current_frame_tracks_for_manager = []
        if results and results[0].boxes is not None and results[0].boxes.id is not None:
            for box in results[0].boxes:
                if int(box.cls[0]) in config['car_class_id']:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    bbox_center_x, bbox_center_y = get_bbox_center([x1, y1, x2, y2])
                    
                    if is_point_in_any_polygon((bbox_center_x, bbox_center_y), scaled_parking_zones):
                        current_frame_tracks_for_manager.append({
                            'id': int(box.id[0]),
                            'bbox': np.array([x1, y1, x2, y2]),
                            'conf': float(box.conf[0]),
                            'cls': int(box.cls[0])
                        })

        alerts = car_tracker_manager.update(current_frame_tracks_for_manager, frame_idx, resized_frame)
        
        for alert_msg in alerts:
            logger.info(f"ALERT [{cam_name}]: {alert_msg}")

        parking_data_to_send = car_tracker_manager.get_parking_events_for_api()
        for event in parking_data_to_send:
            event_for_json = event.copy()
            if 'entry_time' in event_for_json and isinstance(event_for_json['entry_time'], datetime):
                event_for_json['entry_time'] = event_for_json['entry_time'].isoformat() + "Z"
            if 'exit_time' in event_for_json and isinstance(event_for_json['exit_time'], datetime):
                event_for_json['exit_time'] = event_for_json['exit_time'].isoformat() + "Z"

            payload_to_send = {
                "parking_violation": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "branch_id": branch_id,
                    "camera_id": camera_id,
                    **event_for_json
                }
            }
            await send_data_to_api(camera_id, payload_to_send, api_key)

        if frame_idx % 150 == 0 and api_retry_queue:
            logger.info(f"[{cam_name}] Found {len(api_retry_queue)} items in retry queue. Resending one.")
            item_to_retry = api_retry_queue.popleft()
            success = await send_data_to_api(camera_id, item_to_retry['payload'], item_to_retry['api_key'])
            if not success:
                api_retry_queue.appendleft(item_to_retry)

        if mot_save_path:
            write_mot_results(mot_save_path, frame_idx, current_frame_tracks_for_manager)

        # ### แก้ไข ###: เรียกใช้ฟังก์ชัน draw_parking_zones
        draw_parking_zones(resized_frame, scaled_parking_zones)
        for track_id, car_info in car_tracker_manager.tracked_cars.items():
            if 'current_bbox' in car_info and car_info['current_bbox'] is not None:
                x1, y1, x2, y2 = map(int, car_info['current_bbox'])
                status_info = car_tracker_manager.get_car_status(track_id, frame_idx)
                status = status_info['status']
                time_parked_str = status_info['time_parked_str']
                text_color, background_color, draw_box_color = (255, 255, 255), (0, 128, 0), (0, 255, 0)
                if status == 'PARKED': background_color, draw_box_color = (0, 128, 0), (0, 255, 0)
                elif status == 'WARNING_PARKED': background_color, draw_box_color = (0, 100, 200), (0, 255, 255)
                elif status == 'VIOLATION': background_color, draw_box_color = (0, 0, 200), (0, 0, 255)
                elif status == 'OUT_OF_ZONE': background_color, draw_box_color = (128, 0, 0), (255, 0, 0)
                elif status == 'MOVING_IN_ZONE': background_color, draw_box_color = (150, 150, 0), (255, 255, 0)
                else: background_color, draw_box_color = (50, 50, 50), (128, 128, 128)
                full_label_text = f"ID:{track_id} {status}"
                if time_parked_str: full_label_text += f" ({time_parked_str})"
                font, font_scale, font_thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1
                (text_width, text_height), baseline = cv2.getTextSize(full_label_text, font, font_scale, font_thickness)
                
                padding_x = 2
                padding_y = 1
                margin_from_bbox = 4
                
                rect_x1 = x1
                rect_x2 = rect_x1 + text_width + padding_x * 2

                frame_width = resized_frame.shape[1]
                if rect_x2 > frame_width:
                    rect_x2 = x2 
                    rect_x1 = rect_x2 - text_width - padding_x * 2

                rect_y1 = y2 + margin_from_bbox
                rect_y2 = rect_y1 + text_height + padding_y * 2 + baseline
                
                if rect_y2 > resized_frame.shape[0]:
                    rect_y2 = y1 - margin_from_bbox
                    rect_y1 = rect_y2 - (text_height + padding_y * 2 + baseline)

                if draw_bounding_box:
                    cv2.rectangle(resized_frame, (x1, y1), (x2, y2), draw_box_color, 2)

                if rect_x2 > rect_x1 and rect_y2 > rect_y1:
                    cv2.rectangle(resized_frame, (rect_x1, rect_y1), (rect_x2, rect_y2), background_color, -1)
                    cv2.putText(resized_frame, full_label_text, (rect_x1 + padding_x, rect_y1 + text_height + padding_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
        
        current_parked_cars_count = len(car_tracker_manager.get_current_parking_cars())
        total_parking_sessions_display = car_tracker_manager.get_parking_count()
        frame_height, frame_width = resized_frame.shape[:2]
        font, small_font_scale, small_font_thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        text_total_sessions = f"Total Parking Sessions: {total_parking_sessions_display}"
        (w_total, h_total), _ = cv2.getTextSize(text_total_sessions, font, small_font_scale, small_font_thickness)
        pos_total_y = frame_height - 10
        pos_total_x = frame_width - w_total - 10
        cv2.putText(resized_frame, text_total_sessions, (pos_total_x, pos_total_y), font, small_font_scale, (255, 255, 255), small_font_thickness)
        text_current_parked = f"Current Parked: {current_parked_cars_count}"
        (w_parked, _), _ = cv2.getTextSize(text_current_parked, font, small_font_scale, small_font_thickness)
        pos_parked_y = pos_total_y - h_total - 5
        pos_parked_x = frame_width - w_parked - 10
        cv2.putText(resized_frame, text_current_parked, (pos_parked_x, pos_parked_y), font, small_font_scale, (255, 255, 255), small_font_thickness)
        text_cam_name = f"{cam_name}"
        (w_cam, h_cam), _ = cv2.getTextSize(text_cam_name, font, small_font_scale, small_font_thickness)
        pos_cam_y = pos_parked_y - h_cam - 5
        pos_cam_x = frame_width - w_cam - 10
        cv2.putText(resized_frame, text_cam_name, (pos_cam_x, pos_cam_y), font, small_font_scale, (255, 255, 0), small_font_thickness)
        
        end_time = time.time()
        if frame_idx > 1 and frame_idx % (fps * 2) == 0:
            elapsed_time = end_time - start_time
            if elapsed_time > 0:
                actual_processed_frames = fps * 2 / (frames_to_skip if frames_to_skip > 0 else 1)
                worker_fps = actual_processed_frames / elapsed_time
                logger.info(f"[{cam_name}] Worker FPS (Processed): {worker_fps:.2f}")
            start_time = time.time()

        if show_display_flag and resized_frame is not None:
            try:
                display_queue.put((cam_name, resized_frame.copy()))
            except queue.Full:
                logger.warning(f"[{cam_name}] Display queue is full.")
        
        if video_writer and video_writer.isOpened():
            video_writer.write(resized_frame)

    cap.release()
    if video_writer:
        video_writer.release()
    
    final_stats_data = car_tracker_manager.get_all_parking_sessions_data(frame_idx)
    stats_queue.put((cam_name, final_stats_data))
    
    logger.info(f"[{cam_name}] Worker has stopped.")

# --- Wrapper function for multiprocessing.Process (โค้ดเดิม) ---
def camera_worker(cam_cfg, config, display_queue, stats_queue, show_display_flag):
    try:
        asyncio.run(camera_worker_async(cam_cfg, config, display_queue, stats_queue, show_display_flag))
    except Exception as e:
        logger.critical(f"Critical error in camera_worker for {cam_cfg.get('name', 'N/A')}. Process will exit. Error: {e}", exc_info=True)
