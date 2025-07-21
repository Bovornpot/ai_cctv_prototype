โหลดไฟล์ model สำหรับ Re-id รถได้ที่ลิ้งค์นี้
https://drive.google.com/drive/folders/1axWgEZHUYCQj8PD0FLrpcxKBaR4qGi2D?usp=sharing

ระบบ AI CCTV ตรวจจับที่จอดรถ
โปรเจกต์นี้ใช้ YOLOv8 และ DeepOCSORT ในการตรวจสอบพื้นที่จอดรถจากกล้องหลายแหล่ง, ตรวจจับการจอดรถที่ผิดกฎ, และส่งข้อมูลไปยัง API ส่วนกลางเพื่อการวิเคราะห์

สิ่งที่ต้องมีก่อนติดตั้ง (Prerequisites)
ติดตั้ง Anaconda หรือ Miniconda

Python 3.8 ขึ้นไป

ขั้นตอนการติดตั้ง (Installation)
ทำตามขั้นตอนต่อไปนี้เพื่อตั้งค่าสภาพแวดล้อมสำหรับโปรเจกต์บนเครื่องของคุณ

1. โคลนโปรเจกต์ (Clone Repository):

git clone https://github.com/Bovornpot/ai_cctv_prototype.git
cd ai_cctv_prototype/AI%20DEV


2. สร้างและเปิดใช้งาน Conda Environment:

คำสั่งนี้จะสร้าง Environment แยกสำหรับโปรเจกต์นี้โดยเฉพาะ เพื่อป้องกันปัญหาขัดแย้งกับโปรเจกต์ Python อื่นๆ

# สร้าง Environment ชื่อ 'car_parking_env'
conda create --name car_parking_env python=3.9 -y

# เปิดใช้งาน Environment
conda activate car_parking_env


3. ติดตั้ง Library ที่จำเป็นทั้งหมด:

คำสั่งนี้จะอ่านไฟล์ requirements.txt และทำการติดตั้ง Library ที่จำเป็นทั้งหมดตามเวอร์ชันที่ใช้ในการพัฒนาโดยอัตโนมัติ

pip install -r requirements.txt


การตั้งค่า (Configuration)
แก้ไขไฟล์ config.yaml:

อัปเดตส่วน video_sources ให้เป็นที่อยู่ของไฟล์วิดีโอหรือสตรีมกล้องของคุณ

ตรวจสอบให้แน่ใจว่า api_key ตรงกับค่า EXPECTED_API_KEY ในฝั่ง Backend Server

แก้ไขไฟล์ boxmot/configs/deepocsort.yaml:

ปรับค่าพารามิเตอร์ของ Tracker เช่น max_age หากคุณพบปัญหาในการติดตามวัตถุ

การรันโปรแกรม (Running the Application)
คุณต้องรัน Backend Server ก่อน จากนั้นจึงรัน Client ที่ใช้ในการประมวลผล

1. รัน Backend API Server:
เปิด Terminal ใหม่, เปิดใช้งาน Environment (conda activate car_parking_env), และรันคำสั่ง:

uvicorn main:app --reload


Server จะพร้อมใช้งานที่ http://127.0.0.1:8000

2. รันโปรแกรม AI Parking Monitor:
เปิด Terminal อีกอัน, เปิดใช้งาน Environment, และรันคำสั่ง:

python main_monitor.py --show-display


ใช้ --show-display เพื่อดูผลลัพธ์วิดีโอแบบเรียลไทม์

