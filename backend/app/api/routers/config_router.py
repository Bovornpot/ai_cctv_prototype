# app/api/routers/config_router.py
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse
import yaml
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional
from pathlib import Path as PPath
import re

import cv2
import json
import logging

router = APIRouter()

# # กำหนด Path ของไฟล์ config.yaml แบบ Relative
# path_to_config_file = PPath(__file__).resolve().parent.parent.parent.parent / "config.yaml"
path_to_config_file = PPath(__file__).resolve().parent.parent.parent.parent.parent / "config.yaml"

# ===================
# === Pydantic Models ===
class VideoSource(BaseModel):
    name: str
    branch: str
    source_path: str
    parking_zone_file: str
    branch_id: str
    camera_id: str


class DebugSettings(BaseModel):
    enabled: bool
    mock_violation_minutes: int


class PerformanceSettings(BaseModel):
    target_inference_width: int
    frames_to_skip: int
    draw_bounding_box: bool


class ConfigModel(BaseModel):
    model_path: str
    yolo_model: str
    img_size: List[int] = Field(..., min_items=1, max_items=2)
    conf_threshold: float = Field(..., ge=0.0, le=1.0)
    iou_threshold: float = Field(..., ge=0.0, le=1.0)
    agnostic_nms: bool = Field(default=False, description="True = ตรวจจับทุก class แบบไม่แยกชนิด")
    max_det: int = Field(default=300, ge=1, description="จำนวน object สูงสุดที่ detect ต่อ frame")
    augment: bool = Field(default=False, description="True = ใช้ data augmentation ตอน infer")
    reid_model: str
    boxmot_config_path: str
    detection_confidence_threshold: float = Field(..., ge=0.0, le=1.0)
    car_class_id: List[int]
    tracking_method: Literal['deepocsort', 'botsort', 'strongsort']
    per_class_tracking: bool
    debug_settings: DebugSettings
    parking_time_limit_minutes: int
    parking_time_threshold_seconds: int
    grace_period_frames_exit: int
    parked_car_timeout_seconds: int
    movement_threshold_px: int
    movement_frame_window: int
    output_dir: str
    device: Literal['cpu', 'cuda']
    half_precision: bool
    api_key: str
    display_combined_max_width: int
    display_combined_max_height: int
    queue_max_size: int
    save_video: bool
    save_mot_results: bool
    enable_brightness_adjustment: bool
    brightness_method: Literal['clahe', 'histogram']
    video_sources: List[VideoSource]
    performance_settings: PerformanceSettings


# === Backend override (ใช้เฉพาะ backend, ไม่เขียนลงไฟล์) ===
backend_override = {
    "img_size": [960],
    "agnostic_nms": False,
    "max_det": 300,
    "augment": False,
}


# === Helper Functions ===
def load_config() -> ConfigModel:
    """โหลด config.yaml และแปลงเป็น ConfigModel"""
    if not path_to_config_file.exists():
        raise FileNotFoundError(f"Config file not found: {path_to_config_file}")
    with open(path_to_config_file, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f) or {}
    return ConfigModel(**raw_data)


def get_merged_config_dict() -> dict:
    """รวม config จากไฟล์ + backend_override"""
    config = load_config()
    return {**config.model_dump(by_alias=False), **backend_override}


# === Pydantic Models สำหรับ ROI ===
class RoiSetData(BaseModel):
    id: str
    points: List[List[float]]
    name: Optional[str] = None


class MultipleROIPointsData(BaseModel):
    camera_id: str
    roi_sets: List[RoiSetData]


# === Helper Function สำหรับ ROI ===
def resolve_parking_zone_file_path(parking_zone_filename: str) -> PPath:
    if PPath(parking_zone_filename).is_absolute():
        return PPath(parking_zone_filename)
    else:
        base_project_dir = path_to_config_file.parent
        ai_folder_path = base_project_dir / "AI"
        return ai_folder_path / parking_zone_filename


# ===================
# === Endpoints ===
@router.get("/config")
async def get_config():
    try:
        if not path_to_config_file.exists():
            raise HTTPException(status_code=404, detail=f"Config file not found at path: {path_to_config_file}")
        with open(path_to_config_file, "r", encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        # รวม override ให้ backend ใช้
        return {**config_data, **backend_override}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading config.yaml: {str(e)}")
        

@router.post("/config")
async def save_config(config: ConfigModel):
    try:
        # save เฉพาะ config ที่มาจาก frontend
        config_dict = config.model_dump(by_alias=False)
        with open(path_to_config_file, "w", encoding='utf-8') as f:
            yaml.dump(config_dict, f, sort_keys=False)
        return JSONResponse(content={"message": "Config saved successfully to config.yaml"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@router.get("/video-frame/{camera_id}", response_class=Response)
async def get_video_frame(camera_id: str, skip: int = 30):
    """
    ดึงภาพจากวิดีโอ/RTSP ของกล้องตาม camera_id
    skip = จำนวนเฟรมที่จะข้ามก่อนดึงเฟรมจริง (default = 10)
    """
    try:
        if not path_to_config_file.exists():
            raise HTTPException(status_code=404, detail="Config file not found.")

        with open(path_to_config_file, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        source_path_str = None
        for source in config.get("video_sources", []):
            if source.get("camera_id") == camera_id:
                _source_path = source.get("source_path")
                if _source_path:
                    if re.match(r'^(http|https|rtsp)://', _source_path):
                        source_path_str = _source_path
                    else:
                        resolved_path = PPath(_source_path)
                        if not resolved_path.is_absolute():
                            base_project_dir = path_to_config_file.parent.parent
                            resolved_path = base_project_dir / resolved_path
                        if not resolved_path.exists():
                            raise HTTPException(
                                status_code=404,
                                detail=f"Video file not found at path: {resolved_path}"
                            )
                        source_path_str = str(resolved_path)
                break

        if not source_path_str:
            raise HTTPException(status_code=404, detail=f"Video source not found for camera_id: {camera_id}")

        cap = cv2.VideoCapture(source_path_str, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            raise HTTPException(status_code=500, detail=f"Could not open video source from path/url: {source_path_str}")

        # ข้ามเฟรมตามค่า skip
        frame = None
        ret = False
        for _ in range(skip):
            ret, frame = cap.read()
            if not ret:
                continue

        cap.release()

        if not ret or frame is None:
            raise HTTPException(status_code=500, detail="Could not read video frame after skipping frames.")

        _, buffer = cv2.imencode('.jpeg', frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except Exception as e:
        logging.error(f"Error in get_video_frame for {camera_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting video frame: {str(e)}")



@router.get("/roi/polygons/{camera_id}")
async def get_roi_polygons(camera_id: str):
    """โหลด ROI สำหรับกล้องและ return เป็น list ของ polygons"""
    try:
        if not path_to_config_file.exists():
            raise HTTPException(status_code=404, detail="Config file not found.")

        with open(path_to_config_file, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        parking_zone_filename = None
        for source in config.get("video_sources", []):
            if source.get("camera_id") == camera_id:
                parking_zone_filename = source.get("parking_zone_file")
                break

        if not parking_zone_filename:
            return []

        parking_zone_file_path = resolve_parking_zone_file_path(parking_zone_filename)
        if not parking_zone_file_path.exists():
            return []

        with open(parking_zone_file_path, 'r', encoding='utf-8') as f:
            roi_data = json.load(f)

        # ตรวจสอบว่า roi_data เป็น list ของ polygons หรือไม่
        if isinstance(roi_data, list):
            return roi_data
        elif "roi_sets" in roi_data:
            return [
                [[int(p[0]), int(p[1])] for p in roi_set["points"]]
                for roi_set in roi_data["roi_sets"]
            ]
        elif "roi_points" in roi_data:
            return [[[int(p[0]), int(p[1])] for p in roi_data["roi_points"]]]
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading ROI polygons: {str(e)}")


@router.post("/roi", status_code=status.HTTP_201_CREATED)
async def save_roi_polygons(camera_id: str, polygons: List[List[List[int]]]):
    try:
        with open(path_to_config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        parking_zone_filename = None
        for source in config.get("video_sources", []):
            if source.get("camera_id") == camera_id:
                parking_zone_filename = source.get("parking_zone_file")
                break

        if not parking_zone_filename:
            raise HTTPException(status_code=404, detail=f"Camera ID {camera_id} not found in config")

        file_path = resolve_parking_zone_file_path(parking_zone_filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # save JSON as list of polygons
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(polygons, f, ensure_ascii=False, indent=4)

        return {"status": "success", "message": "ROI polygons saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
