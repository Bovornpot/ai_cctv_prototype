import sqlite3
from typing import List, Dict, Any, Optional
import json

DATABASE_URL = "data/db.sqlite" #Path batabase data folder

def get_db_connection(): #connect and return object to the SQLite database
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row #เข้าถึงได้ด้วยชื่อคอลัมน์
    return conn

def create_tables():
    #Creates database tables if they don't exist
    conn = get_db_connection()
    cursor = conn.cursor() #ใช้run คำสั่ง SQL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inference_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        camera_id TEXT NOT NULL,
        total_people INTEGER NOT NULL,
        detections TEXT, -- Store JSON string of additional info
        additional_info TEXT, -- store JSON string of additional info
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP              
        );
    """)
    conn.commit()
    conn.close()

def insert_inference_result(data: Dict[str, Any]): 
    #insert AI result data to inference_results tables
    conn = get_db_connection()
    cursor = conn.cursor()

    #convert dict to JSON strings for storage
    detections_json = json.dumps(data.get("detections",[]))
    additional_info_json = json.dumps(data.get("additional_info", {}))

    cursor.execute("""
        INSERT INTO inference_results (timestamp, camera_id, total_people, detections, additional_info)
        VALUES (?, ?, ?, ?, ?);
    """,(
        data["timestamp"],
        data["camera_id"],
        data["total_people"],
        detections_json,
        additional_info_json
    ))
    conn.commit()
    conn.close()

def get_inference_results(camera_id: Optional[str] = None, limit: int = 100) -> List[Dict[str,Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM inference_results"
    params = []
    
    if camera_id:
        query += " WHERE camera_id = ?"
        params.append(camera_id)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params) #run SQL
    rows = cursor.fetchall() #ดึงข้อมูลที่ตรงกับ SQL
    conn.close()

    results = []
    
    for row in rows:
        result_dict = dict(row) #convert sqlite3.row object to a standard dictionary

        #convert JSON back to python objects เพื่อให้ข้อมูลพร้อมใช้สำหรับ Pydantic Schema
        if 'detections' in result_dict and result_dict['detections']:
            result_dict['detections'] = json.loads(result_dict['detections'])

        if 'additional_info' in result_dict and result_dict['additional_info']:
            result_dict['additional_info'] = json.loads(result_dict['additional_info'])
        results.append(result_dict)

    return results

if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    print(f"Database created at {DATABASE_URL}")





    