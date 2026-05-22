from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.api.deps import get_current_active_user, check_role
from app.core.audit import log_action
from app.core.caching import get_cached_val, set_cached_val, invalidate_dashboard_cache
from app.core.rate_limiter import RateLimiter

router = APIRouter()

@router.get("/metrics", dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregated strategic metrics for the user's active company dashboard.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return {
            "competitor_count": 0,
            "event_count": 0,
            "activity_score": 0,
            "growth_score": 0,
            "severe_events_count": 0
        }
        
    cache_key = f"dashboard:metrics:company_{company.id}"
    cached_metrics = get_cached_val(cache_key)
    if cached_metrics is not None:
        return cached_metrics
        
    # Get competitor IDs
    competitor_ids = [c.id for c in company.competitors]
    if not competitor_ids:
        metrics_data = {
            "competitor_count": 0,
            "event_count": 0,
            "activity_score": 0,
            "growth_score": 0,
            "severe_events_count": 0
        }
        set_cached_val(cache_key, metrics_data, ttl=300)
        return metrics_data
        
    # Competitor count
    competitor_count = len(competitor_ids)
    
    # Event count
    event_count = db.query(CompetitorEvent).filter(
        CompetitorEvent.competitor_id.in_(competitor_ids)
    ).count()
    
    # Activity score: events in the last 14 days
    two_weeks_ago = datetime.utcnow() - timedelta(days=14)
    activity_count = db.query(CompetitorEvent).filter(
        CompetitorEvent.competitor_id.in_(competitor_ids),
        CompetitorEvent.created_at >= two_weeks_ago
    ).count()
    activity_score = min(activity_count * 12, 100) # scale to 100 max
    
    # Growth / Severity score
    severe_events_count = db.query(CompetitorEvent).filter(
        CompetitorEvent.competitor_id.in_(competitor_ids),
        CompetitorEvent.severity == "high"
    ).count()
    
    # Base competitor score: calculate based on event severities
    # High: 15, Medium: 10, Low: 5
    events = db.query(CompetitorEvent.severity, func.count(CompetitorEvent.id)).filter(
        CompetitorEvent.competitor_id.in_(competitor_ids)
    ).group_by(CompetitorEvent.severity).all()
    
    severity_map = dict(events)
    weighted_score = (
        severity_map.get("high", 0) * 15 +
        severity_map.get("medium", 0) * 10 +
        severity_map.get("low", 0) * 5
    )
    growth_score = min(weighted_score, 100)
    
    metrics_data = {
        "competitor_count": competitor_count,
        "event_count": event_count,
        "activity_score": activity_score,
        "growth_score": growth_score,
        "severe_events_count": severe_events_count
    }
    set_cached_val(cache_key, metrics_data, ttl=300)
    return metrics_data

@router.get("/events", response_model=List[Dict[str, Any]], dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def get_recent_events(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch chronological intelligence feed of recent competitor events.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return []
        
    cache_key = f"dashboard:events:company_{company.id}:limit_{limit}"
    cached_events = get_cached_val(cache_key)
    if cached_events is not None:
        return cached_events
        
    competitor_ids = [c.id for c in company.competitors]
    if not competitor_ids:
        set_cached_val(cache_key, [], ttl=300)
        return []
        
    events = db.query(
        CompetitorEvent.id,
        CompetitorEvent.competitor_id,
        CompetitorEvent.event_type,
        CompetitorEvent.title,
        CompetitorEvent.description,
        CompetitorEvent.severity,
        CompetitorEvent.confidence_score,
        CompetitorEvent.created_at,
        Competitor.name.label("competitor_name")
    ).join(
        Competitor, Competitor.id == CompetitorEvent.competitor_id
    ).filter(
        CompetitorEvent.competitor_id.in_(competitor_ids)
    ).order_by(
        CompetitorEvent.created_at.desc()
    ).limit(limit).all()
    
    events_list = [
        {
            "id": e.id,
            "competitor_id": e.competitor_id,
            "competitor_name": e.competitor_name,
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "severity": e.severity,
            "confidence_score": e.confidence_score,
            "created_at": e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else e.created_at
        }
        for e in events
    ]
    
    set_cached_val(cache_key, events_list, ttl=300)
    return events_list

@router.post("/trigger", dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def trigger_intelligence_run(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_role(["admin"]))
):
    """
    Trigger the complete Phase 2 intelligence pipeline: website monitoring, social, news, discovery, and recommendations.
    """
    import os
    import sys
    # Add root directory to path to import agents
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
        
    try:
        from agents.website_monitor import run_monitor_agent
        from agents.social_intelligence import run_social_agent
        from agents.news_agent import run_news_agent
        from agents.market_research import run_market_research_agent
        from agents.recommendation import run_recommendation_agent
      
        company = db.query(Company).filter(Company.user_id == current_user.id).first()
        if not company:
            return {"status": "success", "message": "No active company found. Please onboard first."}
            
        processed_count = 0
        total_events_found = 0
        
        # 1-3. Run competitor-specific scraping & analysis agents
        if company.competitors:
            for competitor in company.competitors:
                if competitor.status == "active":
                    # Agent 1: Website Monitor
                    monitor_state = {
                        "competitor_id": competitor.id,
                        "url": competitor.website,
                        "current_text": "",
                        "previous_text": "",
                        "detected_events": []
                    }
                    monitor_res = run_monitor_agent.invoke(monitor_state)
                    total_events_found += len(monitor_res.get("detected_events", []))
                    
                    # Agent 2: Social Intelligence
                    social_state = {
                        "competitor_id": competitor.id,
                        "company_id": company.id,
                        "competitor_name": competitor.name,
                        "active_platforms": [],
                        "scraped_data": {},
                        "insights_to_save": []
                    }
                    run_social_agent.invoke(social_state)
                    
                    # Agent 3: News Monitoring
                    news_state = {
                        "competitor_id": competitor.id,
                        "company_id": company.id,
                        "competitor_name": competitor.name,
                        "news_articles": [],
                        "insights_to_save": []
                    }
                    run_news_agent.invoke(news_state)
                    
                    processed_count += 1
                    
        # 4. Agent 4: Market Research / Competitor Discovery
        research_state = {
            "company_id": company.id,
            "company_name": company.name,
            "company_industry": company.industry or "Technology",
            "company_services": company.services or "",
            "discovered_competitors": [],
            "insights_to_save": []
        }
        run_market_research_agent.invoke(research_state)
        
        # 5. Agent 5: Recommendation Engine
        recommendation_state = {
            "company_id": company.id,
            "events_to_analyze": [],
            "recommendations_to_save": []
        }
        run_recommendation_agent.invoke(recommendation_state)
        
        log_action(
            db=db,
            user_id=current_user.id,
            action="trigger_swarm",
            details={
                "processed_competitors_count": processed_count,
                "events_captured": total_events_found,
                "company_id": company.id,
                "company_name": company.name
            },
            ip_address=request.client.host if request.client else None
        )
        
        # Invalidate dashboard caches as new events and metrics have been created
        invalidate_dashboard_cache(company.id)
        
        return {
            "status": "success",
            "message": f"Successfully executed strategic analysis pipeline for {processed_count} competitor(s). Generated social/news/market insights and strategic recommendations.",
            "events_captured": total_events_found
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline execution failed: {str(e)}"
        )
