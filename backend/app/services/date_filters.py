from datetime import date
from fastapi import HTTPException

def validate_date_range(start=None,end=None):
    for name,value in [('start_date',start),('end_date',end)]:
        if value:
            try:
                if len(value)!=10 or date.fromisoformat(value).isoformat()!=value:raise ValueError()
            except (ValueError,TypeError):raise HTTPException(422,f'{name} must be a valid YYYY-MM-DD date')
    if start and end and start>end:raise HTTPException(422,'start_date must not exceed end_date')
