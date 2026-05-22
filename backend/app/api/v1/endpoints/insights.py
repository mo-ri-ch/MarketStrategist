from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.insights import Insight
from app.schemas.insights import InsightOut
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[InsightOut])
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all competitor and market insights for the user's active company.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return []
    
    return db.query(Insight).filter(
        Insight.company_id == company.id
    ).order_by(Insight.created_at.desc()).all()

