import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.api.deps import get_current_active_user, check_role
from app.workers.tasks.report_generator import generate_weekly_report
from app.core.audit import log_action
from app.core.rate_limiter import RateLimiter

router = APIRouter()

@router.post("/weekly/trigger", dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def trigger_weekly_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin", "planner"]))
):
    """
    Manually trigger weekly report generation.
    Returns the generated report file as a download response.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company context not found for current user."
        )
        
    try:
        # Run report compilation synchronously to return the file download immediately
        filepath = generate_weekly_report(company.id)
        if not filepath or not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Report compilation failed or did not write output file."
            )
            
        log_action(
            db=db,
            user_id=current_user.id,
            action="generate_weekly_report",
            details={
                "company_id": company.id,
                "company_name": company.name,
                "filepath": filepath
            },
            ip_address=request.client.host if request.client else None
        )
        
        media_type = "application/pdf" if filepath.endswith(".pdf") else "text/html"
        return FileResponse(
            path=filepath,
            filename=os.path.basename(filepath),
            media_type=media_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate and download report: {e}"
        )
