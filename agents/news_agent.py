import os
import sys
import logging
from typing import TypedDict, List, Dict, Any

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from app.db.session import SessionLocal
from app.models.competitor import Competitor
from app.models.insights import Insight
from app.models.events import CompetitorEvent
from app.models.alerts import Alert
from app.services.news_fetcher import fetch_competitor_news

logger = logging.getLogger("news-monitoring-agent")

class AgentState(TypedDict):
    competitor_id: int
    company_id: int
    competitor_name: str
    news_articles: List[Dict[str, Any]]
    insights_to_save: List[Dict[str, Any]]

def fetch_competitor_details(state: AgentState) -> Dict[str, Any]:
    comp_id = state["competitor_id"]
    logger.info(f"[Node: Fetch Competitor Details] Looking up competitor {comp_id}")
    
    db = SessionLocal()
    try:
        competitor = db.query(Competitor).filter(Competitor.id == comp_id).first()
        if not competitor:
            return {"competitor_name": "", "company_id": 0}
        return {
            "competitor_name": competitor.name,
            "company_id": competitor.company_id
        }
    finally:
        db.close()

def gather_news(state: AgentState) -> Dict[str, Any]:
    name = state["competitor_name"]
    logger.info(f"[Node: Gather News] Fetching news for competitor {name}")
    try:
        articles = fetch_competitor_news(name)
        return {"news_articles": articles}
    except Exception as e:
        logger.error(f"Error in gather_news node: {e}")
        return {"news_articles": []}

def generate_news_insights(state: AgentState) -> Dict[str, Any]:
    articles = state["news_articles"]
    name = state["competitor_name"]
    logger.info(f"[Node: Generate News Insights] Analyzing {len(articles)} articles for {name}")
    
    insights = []
    for art in articles:
        category = art.get("category", "general")
        title = art.get("title", f"News Alert: {name}")
        description = art.get("description", "")
        sentiment = art.get("sentiment", 0.0)
        source = art.get("source", "Unknown")
        url = art.get("url", "")
        
        insights.append({
            "insight_type": "news",
            "title": title,
            "description": description,
            "sentiment_score": sentiment,
            "data_points": {
                "source": source,
                "url": url,
                "category": category
            }
        })
        
    return {"insights_to_save": insights}

def save_news_insights(state: AgentState) -> Dict[str, Any]:
    insights = state["insights_to_save"]
    comp_id = state["competitor_id"]
    company_id = state["company_id"]
    
    if not insights:
        logger.info("No news insights to save.")
        return {}
        
    db = SessionLocal()
    saved_event_ids = []
    try:
        for ins in insights:
            # 1. Save to Insight table
            db_insight = Insight(
                company_id=company_id,
                competitor_id=comp_id,
                insight_type=ins["insight_type"],
                title=ins["title"],
                description=ins["description"],
                sentiment_score=ins["sentiment_score"],
                data_points=ins["data_points"]
            )
            db.add(db_insight)
            db.flush()
            
            # 2. If the category is critical (funding, acquisition, partnership, product_launch),
            # write it to CompetitorEvent and trigger alerts via Alert Agent
            category = ins["data_points"].get("category", "general")
            if category in ["funding", "acquisition", "partnership", "product_launch"]:
                db_event = CompetitorEvent(
                    competitor_id=comp_id,
                    event_type="news",
                    title=f"Strategic Event: {ins['title']}",
                    description=ins["description"],
                    confidence_score=0.95,
                    severity="low"  # Default to low, let Alert Agent classify it
                )
                db.add(db_event)
                db.flush()
                saved_event_ids.append(db_event.id)
                
        db.commit()
        logger.info(f"Saved {len(insights)} news insights & associated events to DB for competitor {comp_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving news insights to DB: {e}")
        saved_event_ids = []
    finally:
        db.close()
        
    # Trigger Alert Agent for each saved event
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from alert_agent import run_alert_agent
    for ev_id in saved_event_ids:
        try:
            logger.info(f"Triggering Alert Agent workflow for news event {ev_id}")
            run_alert_agent(ev_id)
        except Exception as ae:
            logger.error(f"Failed to run Alert Agent on news event {ev_id}: {ae}")
        
    return {}

# Define LangGraph graph
workflow = StateGraph(AgentState)

workflow.add_node("fetch_details", fetch_competitor_details)
workflow.add_node("gather_news", gather_news)
workflow.add_node("generate_insights", generate_news_insights)
workflow.add_node("save_insights", save_news_insights)

workflow.set_entry_point("fetch_details")
workflow.add_edge("fetch_details", "gather_news")
workflow.add_edge("gather_news", "generate_insights")
workflow.add_edge("generate_insights", "save_insights")
workflow.add_edge("save_insights", END)

run_news_agent = workflow.compile()
