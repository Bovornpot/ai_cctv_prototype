from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from app import database, schemas
from app.api.deps import get_db, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.InferenceResultResponse, dependencies=[Depends(verify_api_key)])
async def create_inference_result(data: schemas.AnalyticsDataIn, db: Session=Depends(get_db)):
    logger.info(f"Received analytics data")
    try:
        db_item, message = None, "No valid analytics data provided"

        if data.parking_violation:
            db_item = database.DBParkingViolation(**data.parking_violation.model_dump())
            db.add(db_item)
            message = "Parking violation data received."
        elif data.table_occupancy:
            db_item = database.DBTableOccupancy(**data.table_occupancy.model_dump())
            db.add(db_item)
            message = "Table occupancy data received."
        elif data.chilled_basket_alert:
            db_item = database.DBChilledBasketAlert(**data.chilled_basket_alert.model_dump())
            db.add(db_item)
            message = "Chilled basket alert data received."
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid analytics data provided.")

        db.commit()
        db.refresh(db_item)
        return {"message": message, "id": db_item.id}

    except Exception as e:
        db.rollback()
        logging.exception(f"Error processing analytics data:")
        logger.info(f"\n--- DEBUG ERROR START ---")
        logger.info(f"Type of error: {type(e)}")
        logger.info(f"Error details: {e}")
        import traceback
        traceback.print_exc()
        logger.info(f"--- DEBUG ERROR END ---\n")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Failed to process inference result: {e}")