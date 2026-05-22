from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.recommendations import Recommendation
from app.schemas.recommendations import RecommendationOut, RecommendationUpdate
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[RecommendationOut])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all strategic CEO recommendations for the user's active company.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return []
        
    return db.query(Recommendation).filter(
        Recommendation.company_id == company.id
    ).order_by(Recommendation.created_at.desc()).all()

@router.put("/{recommendation_id}", response_model=RecommendationOut)
def update_recommendation(
    recommendation_id: int,
    payload: RecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the status of a strategic recommendation (e.g. pending, implemented, dismissed).
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.company_id == company.id
    ).first()
    
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found or not owned by user company")
        
    if payload.status:
        if payload.status not in ["pending", "implemented", "dismissed"]:
            raise HTTPException(status_code=400, detail="Invalid recommendation status")
        recommendation.status = payload.status
        
    db.commit()
    db.refresh(recommendation)
    return recommendation
