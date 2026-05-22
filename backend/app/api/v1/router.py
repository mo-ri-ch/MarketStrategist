from fastapi import APIRouter
from app.api.v1.endpoints import auth, company, competitors, insights, alerts, chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(competitors.router, prefix="/competitor", tags=["competitor"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
