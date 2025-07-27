from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from app import database, schemas
from app.api.deps import get_db


router = APIRouter(prefix="/chilled_basket_alerts", tags=["Chilled Basket Alerts"])

@router.get("/", response_model= list[schemas.ChilledBasketAlertData],)
def get_chilled_basket_alerts(
    skip: int=0,
    limit: int =100,
    branch_id: Optional[str] = None,
    db: Session= Depends(get_db)
    ):
    query = db.query(database.DBChilledBasketAlert)
    if branch_id:
            query= query.filter(database.DBChilledBasketAlert.branch_id == branch_id)       
    return query.offset(skip).limit(limit).all()
