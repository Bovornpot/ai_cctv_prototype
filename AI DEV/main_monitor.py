# main_monitor.py

import argparse
import multiprocessing
from multiprocessing import Process, Queue
import queue # For handling queue.Empty exception
import cv2
import time
import torch
from pathlib import Path
import sys 
# Import the worker function
from camera_worker_process import camera_worker

# Import your utility functions
from utils import load_config, save_parking_statistics

# ### FIX: เพิ่มฟังก์ชันตรวจสอบ Config ###
def validate_config(config, required_keys):
    """Checks if all required keys are present in the config."""
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        print(f"Error: Missing required keys in config.yaml: {', '.join(missing_keys)}")
        sys.exit(1) # ออกจากโปรแกรมพร้อมแจ้งข้อผิดพลาด

@torch.no_grad() # Keep this decorator if you're certain it's needed for the main process
def run(args):
    # Load config only once in the main Process
    config = load_config(args.config_file)

    # ### FIX: เรียกใช้ฟังก์ชันตรวจสอบ Config ###
    main_required_keys = ['yolo_model', 'reid_model', 'boxmot_config_path', 'api_key', 'video_sources']
    validate_config(config, main_required_keys)

    camera_configs = config.get('video_sources', [])
    if not camera_configs:
        print("Error: No 'video_sources' defined in config.yaml. Please define at least one camera.")
        return

    # Create Queues for inter-process communication
    display_queue = Queue(maxsize=config.get('display_queue_max_size', 10))
    stats_queue = Queue()
    
    processes = []
    
    # Start processes for each camera
    for cam_cfg in camera_configs:
        cam_name = cam_cfg['name']
        source_path = Path(cam_cfg['source_path'])
        roi_file = Path(cam_cfg['parking_zone_file'])

        # Check if source and ROI files exist before creating process (if not URL)
        if not str(source_path).startswith(('rtsp://', 'http://')):
            if not source_path.exists():
                print(f"Error: Video source file '{source_path}' for camera '{cam_name}' not found. Skipping.")
                continue
        if not roi_file.exists():
            print(f"Error: ROI file '{roi_file}' for camera '{cam_name}' not found. Skipping.")
            continue

        p = Process(target=camera_worker, args=(cam_cfg, config, display_queue, stats_queue, args.show_display))
        processes.append(p)
        p.start()

    print("\n--- Starting Multi-Camera Parking Monitor (Multi-processing) ---")
    print(f"Display Streams: {'Enabled' if args.show_display else 'Disabled'}")
    print(f"Save Processed Video: {'Enabled' if config.get('save_video', False) else 'Disabled'}")
    print("Press 'q' to quit.")

    latest_frames = {}
    active_processes = {p.pid: p for p in processes}

    # Main loop for receiving and displaying frames
    while True:
        try:
            cam_name, frame_to_display = display_queue.get(timeout=0.005)
            latest_frames[cam_name] = frame_to_display
            #print(f"[Monitor] Received frame for {cam_name}. latest_frames size: {len(latest_frames)}") 
        except queue.Empty:
            pass 

        if args.show_display:
            if not latest_frames: # <--- เพิ่มการตรวจสอบนี้:
                print("[Monitor] No frames in latest_frames dictionary to display yet.")
            for cam_name, frame_data in latest_frames.items():
                if frame_data is not None:
                    original_width_display = frame_data.shape[1]
                    original_height_display = frame_data.shape[0]
                    display_max_width = 960
                    display_max_height = 540

                    if original_width_display > display_max_width or original_height_display > display_max_height:
                        scale_w = display_max_width / original_width_display
                        scale_h = display_max_height / original_height_display
                        display_scale_factor = min(scale_w, scale_h)
                    else:
                        display_scale_factor = 1.0

                    new_display_width = int(original_width_display * display_scale_factor)
                    new_display_height = int(original_height_display * display_scale_factor)
                    
                    display_frame = cv2.resize(frame_data, (new_display_width, new_display_height))
                    cv2.imshow(f"Car Parking Monitor - {cam_name}", display_frame)
                else:
                    print(f"[Monitor] Frame data for {cam_name} is None, skipping display.") 
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Quitting by user request...")
            break

        for p_id in list(active_processes.keys()): 
            if not active_processes[p_id].is_alive():
                print(f"Process {p_id} for camera has finished.")
                del active_processes[p_id]
        
        if not active_processes:
            print("All camera processes have finished.")
            break

    for p in processes:
        if p.is_alive():
            print(f"Terminating process {p.pid}...")
            p.terminate()
            p.join()

    cv2.destroyAllWindows()
    print("All processes terminated and windows closed.")

    all_parking_stats = {}
    while not stats_queue.empty():
        try:
            cam_name, stats_data = stats_queue.get_nowait()
            all_parking_stats[cam_name] = stats_data
            print(f"Received final stats for {cam_name}")
        except queue.Empty:
            break
    
    # Save all parking statistics (from utils.py)
    if all_parking_stats and config.get('save_parking_stats', False):
        output_dir = Path(config['output_dir'])
        stats_file_path = output_dir / f"parking_stats_{time.strftime('%Y%m%d-%H%M%S')}.json"
        save_parking_statistics(all_parking_stats, stats_file_path)
        print(f"Parking statistics saved to: {stats_file_path}")

    print("Multi-camera monitoring completed.")

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True) # Recommended for Windows

    parser = argparse.ArgumentParser(description="Multi-Camera Car Parking Monitor using YOLOv8 and BoxMOT")
    parser.add_argument("--config-file", type=str, default="config.yaml", help="Path to the configuration file.")
    parser.add_argument("--show-display", action="store_true", help="Display the output video in real-time.")
    parser.add_argument("--save-video", action="store_true", help="Save the output video.") # This arg is used by config, so can be removed if not directly used
    parser.add_argument("--save-mot-results", action="store_true", help="Save tracking results in MOTChallenge format.") # This arg is used by config
    parser.add_argument("--device", type=str, help="Device to run on (e.g., cpu, cuda:0). Overrides config.") # This arg is used by config, so can be removed if not directly used
    args = parser.parse_args()
    
    run(args)