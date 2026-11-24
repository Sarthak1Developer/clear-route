from fastapi import APIRouter,Depends,Query,HTTPException
from datetime import date
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.services.profile_service import profile
router=APIRouter(tags=['Historical statistics'])
@router.get('/analytics/profile')
def get_profile(city:str|None=None,location:str|None=None,start_date:date|None=None,end_date:date|None=None,db:Session=Depends(get_db)):
    if start_date and end_date and start_date>end_date:raise HTTPException(422,"start_date must not exceed end_date")
    return profile(db,city,location,start_date.isoformat() if start_date else None,end_date.isoformat() if end_date else None)
