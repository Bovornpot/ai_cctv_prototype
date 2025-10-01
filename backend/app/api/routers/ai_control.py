from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import asyncio
import subprocess
import signal
import sys
from pathlib import Path
from typing import Set, Optional
import os 
from typing import Set, Optional
router = APIRouter(tags=["AI Control"])

# กำหนด Path แบบ Relative โดยอิงจากตำแหน่งของไฟล์ปัจจุบัน
# =========================================================================================
AI_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "AI"

# แก้ไขบรรทัดนี้เพื่อแปลง str ที่ได้จาก os.path.join() ให้เป็น Path object
PYTHON_EXE = Path(os.path.join(sys.prefix, 'python.exe'))

# เพิ่มบรรทัดนี้ เพื่อให้ Path ไปยัง config.yaml ถูกต้อง
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"

# === ตัวจัดการ WebSocket clients ===
class WSManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.active.add(ws)

    async def disconnect(self, ws: WebSocket):
        async with self.lock:
            self.active.discard(ws)

    async def broadcast(self, text: str):
        async with self.lock:
            dead = []
            for ws in list(self.active):
                try:
                    await ws.send_text(text)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active.discard(ws)

ws_manager = WSManager()

# === สถานะโปรเซส + คิว log ===
PROCESS: Optional[subprocess.Popen] = None
LOG_QUEUE: asyncio.Queue[str] = asyncio.Queue()
READER_TASKS: list[asyncio.Task] = []

# --- ตัวอ่าน stream แล้วส่งเข้า LOG_QUEUE ---
async def _read_stream(stream, name: str):
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, stream.readline)
        if not line:
            break
        await LOG_QUEUE.put(f"[{name}] {line.rstrip()}")
    await LOG_QUEUE.put(f"[{name}] -- stream closed --")

# --- ส่ง log ไปยัง WebSocket clients ---
async def _pump_to_websocket():
    """ ดึง log จาก queue แล้วกระจายให้ทุก client (ทำงานตลอดอายุ server) """
    while True:
        line = await LOG_QUEUE.get()
        await ws_manager.broadcast(line)

# --- สร้างคำสั่งรัน AI ---
def _build_ai_command() -> list[str]:
    return [
        str(PYTHON_EXE),
        # ต้องเปลี่ยน main_monitor.py ให้ใช้ path แบบเต็ม
        str(AI_DIR / "main_monitor.py"), 
        "--config-file", str(CONFIG_FILE_PATH),
        "--show-display"
    ]

# === API Start AI ===
@router.post("/ai/start")
async def start_ai():
    global PROCESS, READER_TASKS
    if PROCESS is not None and PROCESS.poll() is None:
        raise HTTPException(status_code=400, detail="AI is already running.")

    if not AI_DIR.exists():
        raise HTTPException(status_code=400, detail=f"AI_DIR not found: {AI_DIR}")

    if not PYTHON_EXE.exists():
        raise HTTPException(status_code=400, detail=f"Python exe not found: {PYTHON_EXE}")

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        PROCESS = subprocess.Popen(
            _build_ai_command(),
            cwd=str(AI_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
            creationflags=creationflags
        )
    except Exception as e:
        PROCESS = None
        raise HTTPException(status_code=500, detail=f"Failed to start AI: {e}")

    READER_TASKS = [
        asyncio.create_task(_read_stream(PROCESS.stdout, "STDOUT")),
        asyncio.create_task(_read_stream(PROCESS.stderr, "STDERR")),
    ]

    await ws_manager.broadcast("=== AI Process Started ===")
    return {"status": "success", "message": "AI started"}

# === API Stop AI ===
@router.post("/ai/stop")
async def stop_ai():
    global PROCESS, READER_TASKS
    if PROCESS is None or PROCESS.poll() is not None:
        raise HTTPException(status_code=400, detail="AI is not running.")

    try:
        if sys.platform.startswith("win"):
            PROCESS.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            PROCESS.terminate()
    except Exception as e:
        await ws_manager.broadcast(f"[STOP] Failed to signal process: {e}")

    try:
        await asyncio.wait_for(asyncio.to_thread(PROCESS.wait), timeout=10)
    except asyncio.TimeoutError:
        await ws_manager.broadcast("[STOP] Graceful stop timeout. Killing process...")
        try:
            PROCESS.kill()
        except Exception:
            pass
        await asyncio.to_thread(PROCESS.wait)

    for t in READER_TASKS:
        t.cancel()
    READER_TASKS = []
    PROCESS = None

    await ws_manager.broadcast("=== AI Process Stopped ===")
    return {"status": "success", "message": "AI stopped"}

# === API Status AI ===
@router.get("/ai/status")
async def ai_status():
    if PROCESS is None or PROCESS.poll() is not None:
        return {"status": "stopped"}
    return {"status": "running"}

# === WebSocket สำหรับ log ===
@router.websocket("/ws/ai-logs")
async def ai_logs_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_text("--- Connected to AI Log Stream ---")
        while True:
            try:
                # รอข้อความจาก client เผื่อใช้ keepalive
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # ถ้า client ไม่ส่งอะไรมานาน 30s ก็ยังไม่เป็นไร แค่ loop ต่อ
                continue
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket)

# === startup event: สตาร์ท log pump ===
@router.on_event("startup")
async def _on_startup():
    asyncio.create_task(_pump_to_websocket())
