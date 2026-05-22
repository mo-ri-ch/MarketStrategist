from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, UserRoleUpdate
from app.schemas.token import Token
from app.api.deps import get_current_active_user, check_role
from app.core.audit import log_action
from app.core.rate_limiter import RateLimiter

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=True))])
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists in the system.",
        )
    
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role or "viewer",
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=True))])
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Get JWT access token for standard email/password login.
    """
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not security.verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Log audit entry
    log_action(
        db=db,
        user_id=user.id,
        action="login",
        details={"email": user.email},
        ip_address=request.client.host if request.client else None
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserOut, dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def read_user_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current logged in user profile details.
    """
    return current_user


@router.patch("/users/{user_id}/role", response_model=UserOut, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin"]))
):
    """
    Update a user's role. Restricted to administrators.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    allowed_roles = ["admin", "planner", "viewer"]
    if role_update.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of {allowed_roles}"
        )
        
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user


