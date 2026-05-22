from fastapi import APIRouter
from app.api.v1.endpoints import auth, company, competitors, insights, recommendations, alerts, chat, dashboard, predictor, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(competitors.router, prefix="/competitor", tags=["competitor"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(predictor.router, prefix="/predictor", tags=["predictor"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
