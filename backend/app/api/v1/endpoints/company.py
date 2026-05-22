from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate
from app.api.deps import get_current_active_user
from app.services.llm import generate_company_summary

router = APIRouter()

@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def onboard_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Onboard a company profile for the current user and generate an AI strategic summary.
    """
    existing_company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already onboarded a company profile for this account."
        )
    
    # Generate AI summary stub/briefing
    ai_summary = generate_company_summary(
        name=company_in.name,
        website=company_in.website,
        industry=company_in.industry,
        services=company_in.services,
        region=company_in.region,
        goals=company_in.goals
    )
    
    db_company = Company(
        name=company_in.name,
        website=company_in.website,
        industry=company_in.industry,
        services=company_in.services,
        region=company_in.region,
        goals=company_in.goals,
        ai_summary=ai_summary,
        user_id=current_user.id
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/my-company", response_model=CompanyOut)
def get_my_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve the company onboarded by the active user.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user. Please complete onboarding."
        )
    return company

@router.patch("/my-company", response_model=CompanyOut)
def update_my_company(
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the active user's company profile.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user. Please complete onboarding."
        )
    
    update_data = company_in.model_dump(exclude_unset=True) if hasattr(company_in, 'model_dump') else company_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    return company

@router.get("/", response_model=List[CompanyOut])
def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all companies owned by the user.
    """
    companies = db.query(Company).filter(Company.user_id == current_user.id).all()
    return companies

