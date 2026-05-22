import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.api.deps import get_current_active_user
from app.workers.tasks.report_generator import generate_weekly_report

router = APIRouter()

@router.post("/weekly/trigger")
def trigger_weekly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
