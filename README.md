AI CCTV Prototype

โปรเจกต์ต้นแบบ AI CCTV นี้มีเป้าหมายเพื่อพัฒนาระบบเฝ้าระวังอัจฉริยะที่สามารถประมวลผลข้อมูลวิดีโอจากกล้อง IP เพื่อวิเคราะห์ข้อมูลเชิงลึก เช่น การนับจำนวนคน, การประมาณเพศและอายุ, และการสร้าง Heatmap ระบบจะถูกออกแบบมาให้สามารถทำงานได้ทั้งบน Edge Device (สำหรับประมวลผลแบบเรียลไทม์ใกล้แหล่งกำเนิดข้อมูล) และเชื่อมต่อกับ Backend/Frontend บน Cloud/Server เพื่อการจัดเก็บและแสดงผลข้อมูล

Phase1: AI CCTV Prototype - Initial Setup & Camera Capture 

1.Project Structure Overview

ai_cctv_prototype/
├── venv/                   # Python Virtual Environment (ไม่ถูกติดตามโดย Git)
├── .gitignore              # กำหนดไฟล์/โฟลเดอร์ที่ Git จะละเว้น
├── README.md               # เอกสารหลักของโปรเจกต์
├── docker-compose.yml      # (ในอนาคต) สำหรับจัดการ Dockerized Services
├── docs/                   # เอกสารประกอบโปรเจกต์โดยรวม (เช่น สถาปัตยกรรม)
│
├── backend/                # ส่วน Backend (FastAPI/Flask API) - โดย Edge/Full-Stack Engineer
│   ├── app/
│   └── database/
│
├── frontend/               # ส่วน Frontend (React.js Dashboard) - โดย Edge/Full-Stack Engineer
│   ├── public/
│   ├── src/
│   ├── node_modules/
│   ├── package.json
│   └── package-lock.json
│
├── inference_runtime/      # สคริปต์การจับภาพ, รัน Inference, ส่งข้อมูล - โดย Edge/Full-Stack Engineer (และใช้โมเดลจาก AI Engineer)
│   ├── camera_capture/     # สคริปต์ดึงเฟรมจากกล้อง/วิดีโอ
│   ├── inference_wrapper/  # สคริปต์สำหรับการโหลด/รันโมเดล AI (mock/จริง)
│   ├── configs/            # ไฟล์การตั้งค่าต่างๆ
│   └── models/             # (AI Engineer จะวางไฟล์โมเดล AI ที่นี่)
│
├── ai_development/         # สำหรับการพัฒนา, ฝึกฝน, ประเมินโมเดล AI - โดย AI/Computer Vision Engineer
│   ├── datasets/
│   ├── models/
│   ├── notebooks/
│   └── scripts/
│
└── data/                   # สำหรับไฟล์ข้อมูลที่ไม่ต้องการ Commit (เช่น SQLite DB, logs)
    ├── db.sqlite
    └── logs/

2.Environment Setup
    2.1) Prerequisites
        - Python 3.10.11
        - Node.js & npm
        - Git
    2.2) Installing
        1.โคลน Repository
            git clone https://github.com/Bovornpot/ai_cctv_prototype.git

        2.ตั้งค่า Git User
            git config --global user.name "Bovornpot"
            git config --global user.email "bovornpot5861@gmail.com"
        
        3.สร้างและ Activate Python Virtual Environment
            python -m venv venv # สำหรับ Windows
        
        4.ติดตั้ง Python Dependencies สำหรับส่วนต่างๆ
            - สำหรับ inference_runtime (Camera Capture): 
                pip install opencv-python-headless opencv-python 

            - สำหรับ backend (FastAPI/Flask)
                pip install fastapi uvicorn pandas numpy

        5.ติดตั้ง Node.js Dependencies สำหรับ frontend:
            cd frontend
            npm install     

3.Video Capture (Test)
    ใน Week แรก ยังไม่ได้ใช้การดึง Live IP Camera แต่ใช้ วิดีโอแทน
    3.1) เตรียมไฟล์วิดีโอ นามสกุล .mp4

    3.2) rtsp_capture.py: เปิดไฟล์ inference_runtime/camera_capture/rtsp_capture.py และเปลี่ยนค่า rtsp_url ให้เป็น Path ของไฟล์วิดีโอ หรือเป็น RTSP URL ของกล้อง IP
            # ตัวอย่างการใช้ไฟล์วิดีโอ
             rtsp_url = r"C:\Users\bovornpotpua\Desktop\example.mp4"

            # ตัวอย่างการใช้ Live Stream จากกล้อง
             rtsp_url = "rtsp://<username>:<password>@<camera_ip_address>:<port>/<stream_path>" 

    3.3) รันสคริปต์: ตรวจสอบให้แน่ใจว่าคุณอยู่ใน Python Virtual Environment ((venv) นำหน้า Command Prompt) แล้วรันคำสั่ง:
            python inference_runtime/camera_capture/rtsp_capture.py

(start 09/06/2056 - finish 09/06/2025)

Phase 2: การจำลอง AI Inference, Backend API
    1. การนิยามโครงสร้างข้อมูล (Output JSON Schema)
        เราได้กำหนดรูปแบบมาตรฐานของข้อมูลผลลัพธ์จาก AI Inference โดยใช้ Pydantic Models ในไฟล์ backend/app/schemas.py ซึ่งทำหน้าที่เป็น "สัญญาข้อมูล" เพื่อให้แน่ใจว่าข้อมูลที่ถูกส่งและรับในระบบมีรูปแบบที่ถูกต้องและสอดคล้องกัน
        - ไฟล์: backend/app/schemas.py
        - ประโยชน์: ช่วยให้ FastAPI สามารถตรวจสอบความถูกต้องของข้อมูลขาเข้าและสร้างเอกสาร API ได้โดยอัตโนมัติ

    2. Mock AI Inference Script (การจำลองผลลัพธ์ AI)
        เราได้สร้างสคริปต์จำลองในไฟล์ inference_runtime/inference_wrapper/mock_ai_inference.py ที่สร้างข้อมูลผลลัพธ์การวิเคราะห์ AI แบบสุ่ม (เช่น จำนวนคน, ตำแหน่งการตรวจจับ, ID กล้อง) ในรูปแบบ JSON
        - ไฟล์: inference_runtime/inference_wrapper/mock_ai_inference.py
        - ประโยชน์: ใช้สำหรับพัฒนาและทดสอบระบบ Backend โดยไม่ต้องพึ่งพา AI Model หรือฮาร์ดแวร์จริง ทำให้การพัฒนาเป็นไปอย่างรวดเร็ว

    3. Database Module (SQLite)
        เราได้พัฒนาโมดูลสำหรับการจัดการฐานข้อมูลโดยใช้ SQLite ในไฟล์ backend/app/database.py ซึ่งเป็นฐานข้อมูลแบบไฟล์เดียวที่เหมาะสำหรับโปรเจกต์ต้นแบบและ Edge Device
        - ไฟล์: backend/app/database.py
        - ความสามารถ: 
            จัดการการเชื่อมต่อกับฐานข้อมูล data/db.sqlite
            สร้างตาราง inference_results เพื่อจัดเก็บข้อมูลการวิเคราะห์ AI
            ฟังก์ชันสำหรับบันทึก (Insert) ผลลัพธ์ AI ใหม่
            ฟังก์ชันสำหรับดึง (Retrieve) ผลลัพธ์ AI ล่าสุด หรือกรองตาม ID กล้อง

    4.FastAPI Application (Backend API)
        เราได้สร้างหัวใจหลักของระบบ Backend ด้วย FastAPI ในไฟล์ backend/app/main.py ซึ่งทำหน้าที่เป็นจุดรับและส่งข้อมูลหลักของระบบ
        - ไฟล์: backend/app/main.py
        - ความสามารถ:
            - CORS Middleware: อนุญาตให้ Frontend สามารถเรียกใช้ API ได้อย่างปลอดภัย
            - Startup Event: สร้างโฟลเดอร์ data และตรวจสอบ/สร้างตารางฐานข้อมูลโดยอัตโนมัติเมื่อ API เริ่มทำงาน
            - Health Check Endpoint (/health): สำหรับตรวจสอบสถานะการทำงานของ API
            - POST Endpoint (/inference_results/):
                - รับข้อมูลผลลัพธ์ AI จาก Edge Device (จำลองโดย mock_ai_inference.py)
                - ใช้ Pydantic เพื่อ Validate ข้อมูลขาเข้า โดยอัตโนมัติ
                - จัดเก็บข้อมูลลงในฐานข้อมูลผ่าน database.py
            - GET Endpoint (/inference_results/):
                - ดึงข้อมูลผลลัพธ์ AI ล่าสุดจากฐานข้อมูล
                - รองรับการกรองตาม camera_id และการจำกัดจำนวนผลลัพธ์ (limit)
            - Interactive API Documentation: FastAPI สร้างเอกสาร API (Swagger UI) ที่ http://127.0.0.1:8000/docs โดยอัตโนมัติ ทำให้คุณสามารถสำรวจและทดสอบ API ได้อย่างง่ายดาย
            



    