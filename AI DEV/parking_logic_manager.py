# parking_logic_manager.py
import time
import json
from pathlib import Path
import cv2
import numpy as np
from collections import deque # <<< NEW: Import deque

# สามารถเพิ่มหรือปรับเปลี่ยนโครงสร้างของคลาสนี้ตามความต้องการของ logic การจอดรถของคุณ
# นี่คือตัวอย่างโครงสร้างพื้นฐาน

class GlobalParkingMonitor:
    """
    Manages the global parking status across all cameras.
    Tracks car states (moving, parked, violation) within defined parking zones.
    """
    def __init__(self, parking_zone_polygons_by_camera, parking_time_limit_minutes=15, movement_threshold_px=5.0, movement_frame_window=10):
        # NEW: parking_zone_polygons_by_camera is now a dictionary {camera_id: parking_zone_polygon_coords_list}
        self.parking_zone_polygons_by_camera = parking_zone_polygons_by_camera
        self.parking_time_limit_ms = parking_time_limit_minutes * 60 * 1000 # Convert minutes to milliseconds

        self.movement_threshold_px = movement_threshold_px
        self.movement_frame_window = movement_frame_window

        # Global storage for car states
        # Key: global_track_id
        # Value: {
        #    'latest_bbox': [...],
        #    'cls': int,
        #    'history_bboxes_centers': deque([(center_x, center_y, timestamp_ms), ...]),
        #    'is_in_parking_zone': bool,
        #    'parking_start_time_ms': float or None,
        #    'current_status': str ('UNKNOWN', 'IN ZONE (Moving)', 'STATIONARY (Zone)', 'PARKED', 'VIOLATION', 'OUT OF ZONE'),
        #    'last_seen_timestamp_ms': float
        # }
        self.car_states = {}
        self.parking_sessions = [] # For saving historical parking data

    def update_parking_status(self, global_active_tracks, current_timestamp_ms):
        """
        Updates the parking status of globally tracked cars.
        Args:
            global_active_tracks (dict): Dictionary of global tracks from GlobalTrackerManager.
            current_timestamp_ms (float): Current timestamp in milliseconds.
        """
        # Iterate through globally active tracks
        for global_id, g_info in global_active_tracks.items():
            # Retrieve camera_id associated with the latest update of this global_id
            # Assuming g_info contains 'last_seen_camera_id'
            last_seen_camera_id = g_info.get('last_seen_camera_id') 

            if last_seen_camera_id is None:
                # If camera_id is not available, we cannot determine parking zone status per camera
                # Handle this case (e.g., skip or assign a default status)
                if global_id not in self.car_states:
                    self.car_states[global_id] = {
                        'latest_bbox': g_info['bbox'],
                        'cls': g_info['cls'],
                        'history_bboxes_centers': deque([], maxlen=self.movement_frame_window),
                        'is_in_parking_zone': False, # Default to False if zone cannot be determined
                        'parking_start_time_ms': None,
                        'current_status': 'UNKNOWN',
                        'last_seen_timestamp_ms': current_timestamp_ms
                    }
                self.car_states[global_id]['latest_bbox'] = g_info['bbox']
                self.car_states[global_id]['last_seen_timestamp_ms'] = current_timestamp_ms
                continue # Skip zone-specific checks

            # Ensure car_state exists
            if global_id not in self.car_states:
                self.car_states[global_id] = {
                    'latest_bbox': g_info['bbox'],
                    'cls': g_info['cls'],
                    'history_bboxes_centers': deque([], maxlen=self.movement_frame_window),
                    'is_in_parking_zone': False, # Will be updated
                    'parking_start_time_ms': None,
                    'current_status': 'UNKNOWN',
                    'last_seen_timestamp_ms': current_timestamp_ms
                }
            
            car_state = self.car_states[global_id]
            car_state['latest_bbox'] = g_info['bbox']
            car_state['last_seen_timestamp_ms'] = current_timestamp_ms
            car_state['history_bboxes_centers'].append(((g_info['bbox'][0] + g_info['bbox'][2]) / 2, (g_info['bbox'][1] + g_info['bbox'][3]) / 2, current_timestamp_ms))

            # Determine if car is in its specific parking zone for the camera it was last seen on
            current_center_x, current_center_y = (g_info['bbox'][0] + g_info['bbox'][2]) / 2, (g_info['bbox'][1] + g_info['bbox'][3]) / 2
            
            # Use the correct parking zone for the last seen camera
            current_parking_zone = self.parking_zone_polygons_by_camera.get(last_seen_camera_id)
            
            is_in_parking_zone_now = False
            if current_parking_zone is not None and len(current_parking_zone) > 0:
                is_in_parking_zone_now = cv2.pointPolygonTest(np.array(current_parking_zone, np.int32), (current_center_x, current_center_y), False) >= 0
            
            car_state['is_in_parking_zone'] = is_in_parking_zone_now

            # Determine movement
            is_moving = self._check_movement(car_state['history_bboxes_centers'])

            # Update status logic
            prev_status = car_state['current_status']

            if not is_in_parking_zone_now:
                # If car moves out of zone, reset parking timer
                if prev_status in ['STATIONARY (Zone)', 'PARKED', 'VIOLATION']:
                    self._end_parking_session(global_id, car_state, current_timestamp_ms)
                car_state['parking_start_time_ms'] = None
                car_state['current_status'] = 'OUT OF ZONE'
            else: # Car is currently IN zone
                if is_moving:
                    # Car is in zone and moving, reset timer
                    if prev_status in ['STATIONARY (Zone)', 'PARKED', 'VIOLATION']:
                        self._end_parking_session(global_id, car_state, current_timestamp_ms)
                    car_state['parking_start_time_ms'] = None
                    car_state['current_status'] = 'IN ZONE (Moving)'
                else: # Car is in zone and stationary
                    if car_state['parking_start_time_ms'] is None:
                        # Start parking timer if just became stationary in zone
                        car_state['parking_start_time_ms'] = current_timestamp_ms
                        car_state['current_status'] = 'STATIONARY (Zone)'
                    else:
                        time_parked = current_timestamp_ms - car_state['parking_start_time_ms']
                        if time_parked > self.parking_time_limit_ms:
                            car_state['current_status'] = 'VIOLATION'
                        else:
                            car_state['current_status'] = 'PARKED' # Or just 'STATIONARY (Zone)' if not parked long enough
            
            # --- Handle cars that are no longer active in global_active_tracks ---
            # This logic should typically be handled by GlobalTrackerManager to remove inactive tracks
            # But here we ensure their status is updated to 'OUT OF ZONE' if they disappear
            # (or log their exit from the system)
            # This check is less about parking status and more about overall track lifecycle.
            # For simplicity, we assume global_active_tracks provides only truly active tracks.


        # Clean up old car states (e.g., if a car disappears for too long)
        # GlobalTrackerManager should handle removing truly lost tracks,
        # but here we can set status to 'OUT OF ZONE' for those not in global_active_tracks anymore.
        inactive_global_ids = [
            gid for gid in self.car_states if gid not in global_active_tracks
        ]
        for global_id in inactive_global_ids:
            car_state = self.car_states[global_id]
            if car_state['current_status'] not in ['OUT OF ZONE', 'UNKNOWN']:
                # End any active parking session
                self._end_parking_session(global_id, car_state, current_timestamp_ms)
            car_state['current_status'] = 'OUT OF ZONE'
            car_state['parking_start_time_ms'] = None # Reset parking time

    def _check_movement(self, history_bboxes_centers):
        """
        Checks if the car has moved significantly based on its history of bounding box centers.
        Args:
            history_bboxes_centers (deque): Deque of (center_x, center_y, timestamp_ms) tuples.
        Returns:
            bool: True if the car is considered moving, False otherwise.
        """
        if len(history_bboxes_centers) < self.movement_frame_window:
            return True # Not enough history to determine if stationary

        # Get centers from the beginning and end of the window
        first_point_x, first_point_y, first_time = history_bboxes_centers[0]
        last_point_x, last_point_y, last_time = history_bboxes_centers[-1]

        # Calculate total distance moved within the window
        distance = np.sqrt((last_point_x - first_point_x)**2 + (last_point_y - first_point_y)**2)
        
        # Calculate time elapsed in seconds
        time_elapsed_sec = (last_time - first_time) / 1000.0
        
        if time_elapsed_sec == 0: # Avoid division by zero
            return False # If no time elapsed, assume not moving (or very fast movement)

        speed_px_per_sec = distance / time_elapsed_sec

        return speed_px_per_sec > self.movement_threshold_px

    def _end_parking_session(self, global_id, car_state, end_timestamp_ms):
        """Records an ended parking session."""
        if car_state['parking_start_time_ms'] is not None:
            start_time = car_state['parking_start_time_ms']
            duration_ms = end_timestamp_ms - start_time
            duration_minutes = duration_ms / (60 * 1000)

            session_type = car_state['current_status'] # e.g., 'PARKED', 'VIOLATION'
            
            # Record the session
            self.parking_sessions.append({
                'global_id': global_id,
                'start_time_ms': start_time,
                'end_time_ms': end_timestamp_ms,
                'duration_minutes': duration_minutes,
                'type': session_type,
                'last_bbox': car_state['latest_bbox'],
                'cls': car_state['cls']
            })
            print(f"Parking session ended for G_ID:{global_id}. Type: {session_type}, Duration: {duration_minutes:.2f} mins.")

    def get_car_status(self, global_id):
        """Returns the current status and time parked string for a given global ID."""
        car_state = self.car_states.get(global_id)
        if car_state:
            status = car_state['current_status']
            time_parked_str = ""
            if status in ['PARKED', 'VIOLATION', 'STATIONARY (Zone)']:
                if car_state['parking_start_time_ms'] is not None:
                    current_time = time.time() * 1000 # Get current time for display
                    time_parked_ms = current_time - car_state['parking_start_time_ms']
                    time_parked_str = f"({time_parked_ms / (60 * 1000):.1f} min)"
            return {'status': status, 'time_parked_str': time_parked_str}
        return {'status': 'UNKNOWN', 'time_parked_str': ''}

    def get_current_parking_cars_count(self):
        """Returns the count of cars currently classified as 'PARKED' or 'VIOLATION'."""
        count = 0
        for state in self.car_states.values():
            if state['current_status'] in ['PARKED', 'VIOLATION', 'STATIONARY (Zone)']:
                count += 1
        return count
    
    def get_total_parking_sessions(self):
        """Returns the total number of recorded parking sessions."""
        return len(self.parking_sessions)

    def save_all_parking_sessions(self, output_dir_path):
        """Saves all recorded parking sessions to a JSON file."""
        output_dir_path.mkdir(parents=True, exist_ok=True)
        timestamp_str = time.strftime("%Y%m%d-%H%M%S")
        output_file = output_dir_path / f"parking_sessions_{timestamp_str}.json"
        
        # Ensure deque objects are converted to list for JSON serialization
        sessions_to_save = []
        for session in self.parking_sessions:
            sessions_to_save.append(dict(session)) # Convert to dict if not already

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sessions_to_save, f, indent=4)
            print(f"Parking sessions saved to {output_file}")
        except Exception as e:
            print(f"Error saving parking sessions to {output_file}: {e}")
