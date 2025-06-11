from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from .schemas import InferenceResult # Import Pydantic model ที่เราสร้างไว้
from .database import create_tables, insert_inference_result, get_inference_results # Import ฟังก์ชันจาก database module
import uvicorn
import os

app = FastAPI(
    title="AI CCTV Prototype Backend API",
    description="API for receiving and serving AI inference results from CCTV streams.",
    version="0.1.0"
)

app.add_middleware( 
    CORSMiddleware,
    allow_origins = ["*"], #ไว้มาแก้ไขเป็นOriginของ Frontend ตอนนี้ให้อนุญาติทั้งหมดไปก่อน
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.on_event("startup") 
def on_startup(): #runs when the FastAPI application starts up.
    os.makedirs("data", exist_ok=True) #Ensures the data directory exists and database tables are created.
    create_tables()
    print("Database tables ensured and ready.")

@app.get("/", response_class=HTMLResponse)
async def read_root(): #Root endpoint that returns a simple HTML welcome page.
    #for checking if api is running

    return """
    <html>
        <head>
            <title>AI CCTV Prototype API</title>
        </head>
        <body>
            <h1>Welcome to AI CCTV Prototype Backend API!</h1>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation (Swagger UI).</p>
            <p>Visit <a href="/redoc">/redoc</a> for alternative API documentation.</p>
        </body>
    </html>
    """

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(): #checking status endpoint
    return {"status": "ok", "message": "API is healthy and operational!"}

@app.post(
    "/inference_results/",
    response_model = dict[str,str],
    status_code = status.HTTP_201_CREATED,
    summary = "Receive and store AI inference results"
)
async def create_inference_result(result: InferenceResult):
    # eceives AI Infernce results from an Edge Device (Inference Runtime) 
    # and stores them into the SQLite database.
    try:
        insert_inference_result(result.model_dump())
        return {"message": "Inference result received and stored successfully!"}
    except Exception as e:
        print(f"Error storing inference result: {e}")
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store inference result: {str(e)}"
        )

@app.get(
    "/inference_results",
    response_model= List[InferenceResult],
    summary= "Retrieve recent AI inference results"
)
async def get_all_inference_results(
    camera_id: Optional[str]= None,
    limit: int =100
):
    #Retrieves recent AI inference results from the database.
    results_from_db= get_inference_results(camera_id=camera_id, limit=limit)
    # Convert fetched rows (which are dicts from database.py) back to Pydantic models for response validation
    return [InferenceResult(**r) for r in results_from_db] 

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload= True, app_dir= "backend")