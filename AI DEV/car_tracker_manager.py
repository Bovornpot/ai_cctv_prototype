#car_tracker_manager.py
import time
from collections import deque
import numpy as np
# ### แก้ไข ###: Import ฟังก์ชันสำหรับหลายโซน
from utils import is_point_in_any_polygon, get_bbox_center
import json
from datetime import datetime, timedelta
import cv2      # ### เพิ่ม ###: สำหรับการจัดการรูปภาพ (Image Processing)
import base64   # ### เพิ่ม ###: สำหรับการเข้ารหัสรูปภาพเป็น Base64

class CarTrackerManager:
    # ### แก้ไข ###: เปลี่ยนชื่อ parameter จาก parking_zone_polygon เป็น parking_zones
    def __init__(self, parking_zones, parking_time_limit_minutes, movement_threshold_px, movement_frame_window, warning_time_limit_minutes, fps, config):
        # ### แก้ไข ###: เก็บเป็นลิสต์ของโซน
        self.parking_zones = [np.array(zone) for zone in parking_zones]
        
        self.movement_threshold_px = movement_threshold_px
        self.movement_frame_window = movement_frame_window
        self.fps = fps
        self.grace_period_frames_exit = int(config.get('grace_period_frames_exit', 5)) 

        # ### เพิ่ม ###: ตรรกะสำหรับโหมดทดสอบ (Debug Mode)
        debug_cfg = config.get('debug_settings', {})
        self.debug_mode_enabled = debug_cfg.get('enabled', False)

        if self.debug_mode_enabled:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!!      DEBUG MODE IS ENABLED         !!!")
            print("!!! Using shorter mock time limits.    !!!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # ใช้เวลาทดสอบที่สั้นลงมาก
            mock_violation_minutes = debug_cfg.get('mock_violation_minutes', 1) # default 1 นาที
            mock_warning_minutes = debug_cfg.get('mock_warning_minutes', 0.5) # default 30 วินาที
            
            self.parking_time_limit_seconds = mock_violation_minutes * 60
            self.warning_time_limit_seconds = mock_warning_minutes * 60
            
            print(f"DEBUG: Violation time set to -> {self.parking_time_limit_seconds} seconds ({mock_violation_minutes} min)")
            print(f"DEBUG: Warning time set to -> {self.warning_time_limit_seconds} seconds ({mock_warning_minutes} min)")
        else:
            # ใช้เวลาจริงจาก config ปกติ
            self.parking_time_limit_seconds = parking_time_limit_minutes * 60
            self.warning_time_limit_seconds = warning_time_limit_minutes * 60

        # tracked_cars stores current state of each car (โค้ดเดิม)
        self.tracked_cars = {} 
        self.parking_sessions_count = 0 
        self.parking_statistics = []
        self.api_events_queue = []

    # ### เพิ่ม ###: ฟังก์ชันสำหรับรีเซ็ตสถานะทั้งหมด เมื่อวิดีโอเริ่มใหม่
    def reset(self):
        """Resets the state of the tracker manager for a new video loop."""
        print("Resetting CarTrackerManager state...")
        self.tracked_cars.clear()
        self.parking_statistics.clear()
        self.api_events_queue.clear()

    def _frame_to_datetime(self, frame_idx, current_frame_datetime=None):
        """Converts a frame index to a datetime object, relative to current_frame_datetime."""
        if current_frame_datetime is None:
            current_frame_datetime = datetime.utcnow()
        """
        Converts a frame index to a datetime object.
        For simplicity, this function now returns the current UTC time,
        as we're capturing actual timestamps directly when events occur.
        If precise historical timestamps are needed, the video's start time
        and frame rate must be used for calculation.
        """
        return datetime.utcnow() # Always return the current UTC time for timestamping events

    # ### แก้ไข ###: เพิ่ม parameter `frame` เข้ามาในเมธอด update (FEATURE 4)
    def update(self, current_tracks, current_frame_idx, frame):
        detected_ids_in_frame = {t['id'] for t in current_tracks}
        alerts = []

        # Update existing tracks and add new ones (โค้ดเดิม)
        for track_data in current_tracks:
            track_id = track_data['id']
            bbox = track_data['bbox']
            conf = track_data['conf']
            cls = track_data['cls']
            bbox_center_x, bbox_center_y = get_bbox_center(bbox)
            
            # ### แก้ไข ###: เรียกใช้ฟังก์ชัน is_point_in_any_polygon และใช้ self.parking_zones
            is_center_in_parking_zone = is_point_in_any_polygon((bbox_center_x, bbox_center_y), self.parking_zones)

            if track_id not in self.tracked_cars:
                # New car detected 
                self.tracked_cars[track_id] = {
                    'current_bbox': bbox,
                    'center_history': deque([(bbox_center_x, bbox_center_y, current_frame_idx)], maxlen=self.movement_frame_window),
                    'last_seen_frame_idx': current_frame_idx,
                    'is_still': False,
                    'is_parking': False,
                    'parking_start_frame_idx': None,
                    'parking_start_time': None,
                    'parking_session_id': None,
                    'has_left_zone': False,
                    'status': 'NEW_DETECTION',
                    'cls': cls,
                    'frames_outside_zone_count': 0,
                    'api_event_sent_parked_start': False,
                    'api_event_sent_warning': False,
                    'api_event_sent_violation': False
                }
            
            car_info = self.tracked_cars[track_id]
            car_info['current_bbox'] = bbox
            car_info['last_seen_frame_idx'] = current_frame_idx
            car_info['center_history'].append((bbox_center_x, bbox_center_y, current_frame_idx))
            
            is_still = self._check_stillness(car_info['center_history'])
            car_info['is_still'] = is_still

            # Parking Logic (โค้ดเดิม)
            if not car_info['is_parking']:
                if is_center_in_parking_zone and is_still:
                    # Car just started parking (โค้ดเดิม)
                    car_info['is_parking'] = True
                    car_info['parking_start_frame_idx'] = current_frame_idx
                    car_info['parking_start_time'] = datetime.utcnow()
                    self.parking_sessions_count += 1
                    car_info['parking_session_id'] = self.parking_sessions_count
                    car_info['has_left_zone'] = False
                    car_info['status'] = 'PARKED'
                    print(f"[{current_frame_idx}] Car ID {track_id} started parking in zone at {car_info['parking_start_time'].isoformat()}.")
                    
                    if not car_info['api_event_sent_parked_start']:
                        current_parked_count = len([c_id for c_id, c in self.tracked_cars.items() if c_id != track_id and c['is_parking'] and c['status'] in ['PARKED', 'WARNING_PARKED', 'VIOLATION']]) + 1
                        
                        self.api_events_queue.append({
                            'event_type': 'parking_started',
                            'car_id': track_id,
                            'current_park': current_parked_count,
                            'total_parking_sessions': self.parking_sessions_count,
                            'entry_time': car_info['parking_start_time'],
                            'duration_minutes': 0.0,
                            'is_violation': False
                        })
                        car_info['api_event_sent_parked_start'] = True

                elif is_center_in_parking_zone and not is_still:
                    car_info['status'] = 'MOVING_IN_ZONE'
                elif not is_center_in_parking_zone:
                    car_info['status'] = 'OUT_OF_ZONE'
            
            elif car_info['is_parking']:
                if not is_center_in_parking_zone:
                    car_info['frames_outside_zone_count'] += 1
                    if car_info['frames_outside_zone_count'] >= self.grace_period_frames_exit:
                        parking_duration_frames = current_frame_idx - car_info['parking_start_frame_idx']
                        parking_duration_s = parking_duration_frames / self.fps
                        parking_duration_min = parking_duration_s / 60.0

                        # ### เพิ่ม ###: ตรรกะการกรองเซสชันที่สั้นกว่า 1 นาที
                        if parking_duration_min < 1.0 and not self.debug_mode_enabled:
                            print(f"[Info] Short parking session ({parking_duration_min:.2f} min) for Car ID {track_id} ignored. Correcting session count.")
                            self.parking_sessions_count -= 1 # แก้ไขยอดรวมให้ถูกต้อง
                        else:
                            is_violation_status = (parking_duration_s > self.parking_time_limit_seconds)
                            status_before_exit = 'VIOLATION_ENDED' if is_violation_status else 'PARKED_ENDED'
                            
                            self.parking_statistics.append({
                                'session_id': car_info['parking_session_id'], 'car_id': track_id,
                                'start_frame': car_info['parking_start_frame_idx'], 'end_frame': current_frame_idx,
                                'duration_frames': parking_duration_frames, 'duration_s': parking_duration_s,
                                'duration_min': parking_duration_min, 'final_status': status_before_exit
                            })
                            print(f"[Parking Ended] Car ID {track_id}, Session ID {car_info['parking_session_id']}: Parked for {parking_duration_s:.2f} seconds.")
                            
                            current_parked_count = len([c_id for c_id, c in self.tracked_cars.items() if c_id != track_id and c['is_parking'] and c['status'] in ['PARKED', 'WARNING_PARKED', 'VIOLATION']])
                            
                            self.api_events_queue.append({
                                'event_type': 'parking_ended', 'car_id': track_id,
                                'current_park': current_parked_count, 'total_parking_sessions': self.parking_sessions_count,
                                'entry_time': car_info['parking_start_time'], 'exit_time': datetime.utcnow(),
                                'duration_minutes': round(parking_duration_min, 2), 'is_violation': is_violation_status
                            })

                        # Reset car's parking state in all cases
                        car_info.update(is_parking=False, parking_start_frame_idx=None, parking_start_time=None,
                                        parking_session_id=None, has_left_zone=True, status='OUT_OF_ZONE',
                                        frames_outside_zone_count=0, api_event_sent_parked_start=False,
                                        api_event_sent_warning=False, api_event_sent_violation=False)
                    else:
                        car_info['status'] = 'OUT_OF_ZONE_GRACE_PERIOD'
                else:
                    car_info['frames_outside_zone_count'] = 0
                    
                    if not is_still:
                        if car_info['parking_start_frame_idx'] is not None:
                            parking_duration_frames = current_frame_idx - car_info['parking_start_frame_idx']
                            parking_duration_s = parking_duration_frames / self.fps
                            parking_duration_min = parking_duration_s / 60.0
                            is_violation_status = (parking_duration_s > self.parking_time_limit_seconds)

                            self.parking_statistics.append({
                                'session_id': car_info['parking_session_id'],
                                'car_id': track_id,
                                'start_frame': car_info['parking_start_frame_idx'],
                                'end_frame': current_frame_idx,
                                'duration_frames': parking_duration_frames,
                                'duration_s': parking_duration_s,
                                'duration_min': parking_duration_min,
                                'final_status': 'PARKED_MOVED_IN_ZONE'
                            })
                            print(f"[Parking Ended - Moved In Zone] Car ID {track_id}, Session ID {car_info['parking_session_id']}: Parked for {parking_duration_s:.2f} seconds.")
                            
                            current_parked_count = len([c_id for c_id, c in self.tracked_cars.items() if c_id != track_id and c['is_parking'] and c['status'] in ['PARKED', 'WARNING_PARKED', 'VIOLATION']])
                            
                            self.api_events_queue.append({
                                'event_type': 'parking_ended_moved',
                                'car_id': track_id,
                                'current_park': current_parked_count,
                                'total_parking_sessions': self.parking_sessions_count,
                                'entry_time': car_info['parking_start_time'],
                                'exit_time': datetime.utcnow(),
                                'duration_minutes': round(parking_duration_min, 2),
                                'is_violation': is_violation_status
                            })

                            car_info['is_parking'] = False
                            car_info['parking_start_frame_idx'] = None
                            car_info['parking_start_time'] = None
                            car_info['parking_session_id'] = None 
                            car_info['has_left_zone'] = False
                            car_info['status'] = 'MOVING_IN_ZONE'
                            car_info['api_event_sent_parked_start'] = False
                            car_info['api_event_sent_warning'] = False
                            car_info['api_event_sent_violation'] = False
                        else:
                            car_info['status'] = 'MOVING_IN_ZONE'
                    else:
                        parking_duration_frames = current_frame_idx - car_info['parking_start_frame_idx']
                        parking_duration_s = parking_duration_frames / self.fps
                        parking_duration_min = parking_duration_s / 60.0
                        
                        if parking_duration_s > self.parking_time_limit_seconds:
                            car_info['status'] = 'VIOLATION'
                            if not car_info['api_event_sent_violation']:
                                alerts.append(f"VIOLATION: Car ID {track_id} parked over {self.parking_time_limit_seconds/60:.2f} minutes ({parking_duration_min:.2f} min).")
                                
                                image_base64 = None
                                try:
                                    x1, y1, x2, y2 = map(int, car_info['current_bbox'])
                                    if x2 > x1 and y2 > y1:
                                        cropped_car = frame[y1:y2, x1:x2]
                                        _, buffer = cv2.imencode('.jpg', cropped_car)
                                        image_base64 = base64.b64encode(buffer).decode('utf-8')
                                        print(f"Successfully captured and encoded image for car ID {track_id}.")
                                    else:
                                        print(f"Warning: Invalid bbox dimensions for car ID {track_id}. Cannot crop image.")
                                except Exception as e:
                                    print(f"ERROR: Could not capture image for car ID {track_id}: {e}")
                                
                                current_parked_count = len(self.get_current_parking_cars())
                                self.api_events_queue.append({
                                    'event_type': 'parking_violation_triggered',
                                    'car_id': track_id, 'current_park': current_parked_count,
                                    'total_parking_sessions': self.parking_sessions_count,
                                    'entry_time': car_info['parking_start_time'],
                                    'duration_minutes': round(parking_duration_min, 2),
                                    'is_violation': True, 'image_base64': image_base64
                                })
                                car_info['api_event_sent_violation'] = True
                        elif parking_duration_s > self.warning_time_limit_seconds:
                            car_info['status'] = 'WARNING_PARKED'
                            if not car_info['api_event_sent_warning']:
                                alerts.append(f"WARNING: Car ID {track_id} parked over {self.warning_time_limit_seconds/60:.2f} minutes ({parking_duration_min:.2f} min).")
                                current_parked_count = len(self.get_current_parking_cars())
                                self.api_events_queue.append({
                                    'event_type': 'parking_warning_triggered',
                                    'car_id': track_id, 'current_park': current_parked_count,
                                    'total_parking_sessions': self.parking_sessions_count,
                                    'entry_time': car_info['parking_start_time'],
                                    'duration_minutes': round(parking_duration_min, 2),
                                    'is_violation': False
                                })
                                car_info['api_event_sent_warning'] = True
                        else:
                            car_info['status'] = 'PARKED'

         # Clean up old tracks (cars that disappeared)
        ids_to_remove = []
        for track_id, car_info in list(self.tracked_cars.items()):
            if track_id not in detected_ids_in_frame:
                if car_info['last_seen_frame_idx'] < current_frame_idx - self.fps * 5:
                    if car_info['is_parking']:
                        parking_duration_frames = current_frame_idx - car_info['parking_start_frame_idx']
                        parking_duration_s = parking_duration_frames / self.fps
                        parking_duration_min = parking_duration_s / 60.0
                        
                        # ### เพิ่ม ###: ตรรกะการกรองเซสชันที่สั้นกว่า 1 นาที
                        if parking_duration_min < 1.0 and not self.debug_mode_enabled:
                            print(f"[Info] Short parking session ({parking_duration_min:.2f} min) for disappeared Car ID {track_id} ignored. Correcting session count.")
                            self.parking_sessions_count -= 1
                        else:
                            is_violation_status = (parking_duration_s > self.parking_time_limit_seconds)
                            status_before_disappeared = 'VIOLATION_DISAPPEARED' if is_violation_status else 'PARKED_DISAPPEARED'
                            self.parking_statistics.append({
                                'session_id': car_info['parking_session_id'], 'car_id': track_id,
                                'start_frame': car_info['parking_start_frame_idx'], 'end_frame': current_frame_idx,
                                'duration_frames': parking_duration_frames, 'duration_s': parking_duration_s,
                                'duration_min': parking_duration_min, 'final_status': status_before_disappeared
                            })
                            print(f"[Parking Ended - Disappeared] Car ID {track_id}, Session ID {car_info['parking_session_id']}: Parked for {parking_duration_s:.2f} seconds.")
                            current_parked_count = len([c_id for c_id, c in self.tracked_cars.items() if c_id != track_id and c['is_parking'] and c['status'] in ['PARKED', 'WARNING_PARKED', 'VIOLATION']])
                            self.api_events_queue.append({
                                'event_type': 'parking_ended_disappeared', 'car_id': track_id,
                                'current_park': current_parked_count, 'total_parking_sessions': self.parking_sessions_count,
                                'entry_time': car_info['parking_start_time'], 'exit_time': datetime.utcnow(),
                                'duration_minutes': round(parking_duration_min, 2), 'is_violation': is_violation_status
                            })
                    ids_to_remove.append(track_id)

        for track_id in ids_to_remove:
            if track_id in self.tracked_cars:
                del self.tracked_cars[track_id]

        return alerts

    def _check_stillness(self, center_history):
        if len(center_history) < self.movement_frame_window: return False
        dist = np.linalg.norm(np.array(center_history[0][:2]) - np.array(center_history[-1][:2]))
        return dist < self.movement_threshold_px

    def get_parking_count(self):
        return self.parking_sessions_count

    def get_current_parking_cars(self):
        parking_statuses = ['PARKED', 'WARNING_PARKED', 'VIOLATION']
        return [id for id, info in self.tracked_cars.items() if info.get('is_parking') and info.get('status') in parking_statuses]
    
    def get_parking_statistics(self):
        return self.parking_statistics

    def get_car_status(self, track_id, current_frame_idx):
        car_info = self.tracked_cars.get(track_id)
        if not car_info: return {'status': 'OUT_OF_SCENE', 'time_parked_str': ''}
        status = car_info.get('status', 'UNKNOWN')
        time_parked_str = ""
        if car_info.get('is_parking') and car_info.get('parking_start_frame_idx') is not None:
            parking_duration_s = (current_frame_idx - car_info['parking_start_frame_idx']) / self.fps
            minutes, seconds = divmod(int(parking_duration_s), 60)
            time_parked_str = f"{minutes:02d}m {seconds:02d}s"
        return {'status': status, 'time_parked_str': time_parked_str}

    def save_all_parking_sessions(self, output_dir, final_frame_idx):
        if output_dir:
            output_file_path = output_dir / "parking_sessions_summary.json"
        else:
            print("Warning: output_dir is None. Cannot save parking sessions to file.")
            return
        
        for track_id, car_info in list(self.tracked_cars.items()):
            if car_info['is_parking']:
                parking_duration_frames = final_frame_idx - car_info['parking_start_frame_idx']
                parking_duration_s = parking_duration_frames / self.fps
                
                status_on_shutdown = car_info['status'] 
                if parking_duration_s > self.parking_time_limit_seconds:
                    status_on_shutdown = 'VIOLATION_SHUTDOWN'
                elif parking_duration_s > self.warning_time_limit_seconds:
                    status_on_shutdown = 'WARNING_SHUTDOWN'
                else:
                    status_on_shutdown = 'PARKED_SHUTDOWN'

                self.parking_statistics.append({
                    'session_id': car_info['parking_session_id'],
                    'car_id': track_id,
                    'start_frame': car_info['parking_start_frame_idx'],
                    'end_frame': final_frame_idx,
                    'duration_frames': parking_duration_frames,
                    'duration_s': parking_duration_s,
                    'duration_min': parking_duration_s / 60.0,
                    'final_status': status_on_shutdown
                })
                print(f"[Parking Ended - App Shutdown] Car ID {track_id}, Session ID {car_info['parking_session_id']}: Parked for {parking_duration_s:.2f} seconds.")
                
                current_parked_count = len([c_id for c_id, c in self.tracked_cars.items() if c_id != track_id and c['is_parking'] and c['status'] in ['PARKED', 'WARNING_PARKED', 'VIOLATION']])
                
                self.api_events_queue.append({
                    'event_type': 'parking_ended_shutdown',
                    'car_id': track_id,
                    'current_park': current_parked_count,
                    'total_parking_sessions': self.parking_sessions_count,
                    'entry_time': car_info['parking_start_time'],
                    'exit_time': datetime.utcnow(),
                    'duration_minutes': round(parking_duration_s / 60.0, 2),
                    'is_violation': (parking_duration_s > self.parking_time_limit_seconds)
                })

        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.parking_statistics, f, indent=4, default=str)
            print(f"All parking sessions saved to {output_file_path}")
        except Exception as e:
            print(f"Error saving parking statistics: {e}")

    def get_final_parking_statistics(self, total_frames):
        all_sessions_for_summary = list(self.parking_statistics) 

        for track_id, car_info in list(self.tracked_cars.items()):
            if car_info['is_parking']:
                parking_duration_frames = total_frames - car_info['parking_start_frame_idx']
                parking_duration_s = parking_duration_frames / self.fps
                
                status_on_summary = car_info['status'] 
                if parking_duration_s > self.parking_time_limit_seconds:
                    status_on_summary = 'VIOLATION_ACTIVE'
                elif parking_duration_s > self.warning_time_limit_seconds:
                    status_on_summary = 'WARNING_ACTIVE'
                else:
                    status_on_summary = 'PARKED_ACTIVE'

                all_sessions_for_summary.append({
                    'session_id': car_info['parking_session_id'],
                    'car_id': track_id,
                    'start_frame': car_info['parking_start_frame_idx'],
                    'end_frame': total_frames,
                    'duration_frames': parking_duration_frames,
                    'duration_s': parking_duration_s,
                    'duration_min': parking_duration_s / 60.0,
                    'final_status': status_on_summary 
                })

        total_sessions = len(all_sessions_for_summary)
        total_duration_s = sum(s['duration_s'] for s in all_sessions_for_summary)
        avg_duration_s = total_duration_s / total_sessions if total_sessions > 0 else 0

        summary_stats = {
            "total_parking_sessions_recorded": total_sessions,
            "average_parking_duration_minutes": avg_duration_s / 60.0,
            "all_sessions_details": all_sessions_for_summary 
        }
        return summary_stats

    def get_parking_events_for_api(self):
        events = list(self.api_events_queue)
        self.api_events_queue.clear()
        return events
