from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.prediction import CompetitorPrediction
from app.schemas.prediction import PredictionOut
from app.api.deps import get_current_active_user
from app.services.predictor import generate_predictions

router = APIRouter()

@router.get("/{competitor_id}", response_model=PredictionOut)
def get_prediction(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve current prediction for a given competitor.
    If none exists, generates one on the fly.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.company_id == company.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found or unauthorized access"
        )
        
    prediction = db.query(CompetitorPrediction).filter(
        CompetitorPrediction.competitor_id == competitor_id
    ).first()
    
    if not prediction:
        try:
            generate_predictions(competitor_id, db=db)
            prediction = db.query(CompetitorPrediction).filter(
                CompetitorPrediction.competitor_id == competitor_id
            ).first()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate prediction on the fly: {e}"
            )
            
    return prediction

@router.post("/{competitor_id}/refresh", response_model=PredictionOut)
def refresh_prediction(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Recalculates the prediction model for a competitor and returns it.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.company_id == company.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found or unauthorized access"
        )
        
    try:
        generate_predictions(competitor_id, db=db)
        prediction = db.query(CompetitorPrediction).filter(
            CompetitorPrediction.competitor_id == competitor_id
        ).first()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh prediction: {e}"
        )
        
    return prediction
