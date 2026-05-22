from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorOut, CompetitorUpdate
from app.api.deps import get_current_active_user, check_role
from app.core.audit import log_action
from app.core.caching import invalidate_dashboard_cache
from app.core.rate_limiter import RateLimiter

router = APIRouter()

@router.post("/", response_model=CompetitorOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def add_competitor(
    competitor_in: CompetitorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin", "planner"]))
):
    """
    Add a new competitor tracking target under an onboarded company.
    Verifies that the target company is owned by the current user.
    """
    company = db.query(Company).filter(
        Company.id == competitor_in.company_id,
        Company.user_id == current_user.id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found or unauthorized access"
        )
    
    existing_competitor = db.query(Competitor).filter(
        Competitor.company_id == competitor_in.company_id,
        Competitor.website == competitor_in.website
    ).first()
    if existing_competitor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A competitor with this website is already registered under this company."
        )

    db_competitor = Competitor(
        company_id=competitor_in.company_id,
        name=competitor_in.name,
        website=competitor_in.website,
        youtube_url=competitor_in.youtube_url,
        instagram_url=competitor_in.instagram_url,
        linkedin_url=competitor_in.linkedin_url,
        facebook_url=competitor_in.facebook_url,
        reddit_url=competitor_in.reddit_url,
        twitter_url=competitor_in.twitter_url,
        medium_url=competitor_in.medium_url,
        threads_url=competitor_in.threads_url,
        region=competitor_in.region or "Global",
        status="active"
    )
    
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)

    log_action(
        db=db,
        user_id=current_user.id,
        action="create_competitor",
        details={"competitor_name": db_competitor.name, "company_id": db_competitor.company_id},
        ip_address=request.client.host if request.client else None
    )

    invalidate_dashboard_cache(db_competitor.company_id)

    return db_competitor

@router.get("/", response_model=List[CompetitorOut], dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def list_competitors(
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all competitors tracked by the current user.
    Can be filtered by a specific company_id.
    """
    query = db.query(Competitor).join(Company).filter(Company.user_id == current_user.id)
    
    if company_id is not None:
        query = query.filter(Competitor.company_id == company_id)
        
    return query.all()

@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def delete_competitor(
    competitor_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin", "planner"]))
):
    """
    Remove a competitor from tracking.
    """
    competitor = db.query(Competitor).join(Company).filter(
        Competitor.id == competitor_id,
        Company.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found or unauthorized access"
        )
        
    competitor_name = competitor.name
    company_id = competitor.company_id
    db.delete(competitor)
    db.commit()

    log_action(
        db=db,
        user_id=current_user.id,
        action="delete_competitor",
        details={"competitor_id": competitor_id, "competitor_name": competitor_name},
        ip_address=request.client.host if request.client else None
    )

    invalidate_dashboard_cache(company_id)

    return None

