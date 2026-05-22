from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.alerts import Alert
from app.schemas.alerts import AlertOut, AlertUpdate
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[AlertOut])
def list_alerts(
    is_read: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve chronological alerts list for the current active user's company.
    Supports filtering by read/unread status.
    """
    # Find user's company
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return []
        
    query = db.query(Alert).join(Competitor).filter(Competitor.company_id == company.id)
    
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)
        
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

@router.put("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a specific alert status (e.g. mark as read).
    """
    alert = db.query(Alert).join(Competitor).join(Company).filter(
        Alert.id == alert_id,
        Company.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or unauthorized access"
        )
        
    if alert_in.is_read is not None:
        alert.is_read = alert_in.is_read
        
    db.commit()
    db.refresh(alert)
    return alert

@router.post("/read-all", status_code=status.HTTP_200_OK)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark all unread alerts as read for the user's company.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    unread_alerts = db.query(Alert).join(Competitor).filter(
        Competitor.company_id == company.id,
        Alert.is_read == False
    ).all()
    
    for alert in unread_alerts:
        alert.is_read = True
        
    db.commit()
    return {"message": f"Successfully marked {len(unread_alerts)} alerts as read."}

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove an alert.
    """
    alert = db.query(Alert).join(Competitor).join(Company).filter(
        Alert.id == alert_id,
        Company.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found or unauthorized access"
        )
        
    db.delete(alert)
    db.commit()
    return None
