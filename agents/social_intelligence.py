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
from app.services.social_scraper import scrape_social_metrics

logger = logging.getLogger("social-intelligence-agent")

class AgentState(TypedDict):
    competitor_id: int
    company_id: int
    competitor_name: str
    active_platforms: List[str]
    scraped_data: Dict[str, Any]
    insights_to_save: List[Dict[str, Any]]

def detect_platforms(state: AgentState) -> Dict[str, Any]:
    comp_id = state["competitor_id"]
    logger.info(f"[Node: Detect Platforms] Finding active channels for competitor {comp_id}")
    
    db = SessionLocal()
    try:
        competitor = db.query(Competitor).filter(Competitor.id == comp_id).first()
        if not competitor:
            return {"active_platforms": [], "competitor_name": "", "company_id": 0}
            
        platforms = []
        if competitor.linkedin_url:
            platforms.append("linkedin")
        if competitor.twitter_url:
            platforms.append("twitter")
        if competitor.youtube_url:
            platforms.append("youtube")
        if competitor.reddit_url:
            platforms.append("reddit")
        if competitor.instagram_url:
            platforms.append("instagram")
        if competitor.medium_url:
            platforms.append("medium")
        if competitor.threads_url:
            platforms.append("threads")
            
        # Default to linkedin if no url is linked to ensure testing works
        if not platforms:
            platforms = ["linkedin"]
            
        return {
            "active_platforms": platforms,
            "competitor_name": competitor.name,
            "company_id": competitor.company_id
        }
    finally:
        db.close()

def gather_social_data(state: AgentState) -> Dict[str, Any]:
    platforms = state["active_platforms"]
    name = state["competitor_name"]
    logger.info(f"[Node: Gather Social] Scraping {len(platforms)} platforms for {name}")
    
    results = {}
    for platform in platforms:
        try:
            data = scrape_social_metrics(name, platform)
            results[platform] = data
        except Exception as e:
            logger.error(f"Error scraping {platform} for {name}: {e}")
            
    return {"scraped_data": results}

def generate_insights(state: AgentState) -> Dict[str, Any]:
    scraped = state["scraped_data"]
    name = state["competitor_name"]
    logger.info(f"[Node: Generate Insights] Processing metrics for {name}")
    
    insights = []
    for platform, data in scraped.items():
        follower_count = data.get("follower_count", 0)
        engagement_rate = data.get("engagement_rate", 0.0)
        avg_sentiment = data.get("avg_sentiment", 0.0)
        posts = data.get("posts", [])
        
        # 1. Base platform summary insight
        insights.append({
            "insight_type": "social",
            "title": f"{platform.capitalize()} Presence Summary - {name}",
            "description": f"Currently tracking {follower_count:,} followers with an engagement rate of {engagement_rate * 100:.1f}%. Overall sentiment of posts is {avg_sentiment:+.2f}.",
            "sentiment_score": avg_sentiment,
            "data_points": {
                "platform": platform,
                "follower_count": follower_count,
                "engagement_rate": engagement_rate,
                "avg_sentiment": avg_sentiment
            }
        })
        
        # 2. Add individual alerts/insights for low/high sentiment posts
        for post in posts:
            sentiment = post.get("sentiment", 0.0)
            text = post.get("post_text", "")
            if sentiment >= 0.5:
                insights.append({
                    "insight_type": "social",
                    "title": f"Positive Update on {platform.capitalize()} by {name}",
                    "description": f"Positive engagement spike: '{text[:120]}...'",
                    "sentiment_score": sentiment,
                    "data_points": {
                        "platform": platform,
                        "likes": post.get("likes", 0),
                        "comments": post.get("comments", 0),
                        "post_text": text
                    }
                })
            elif sentiment <= -0.3:
                insights.append({
                    "insight_type": "social",
                    "title": f"Negative/Critical Sentiment Alert on {platform.capitalize()}",
                    "description": f"Negative sentiment detected from post: '{text[:120]}...'",
                    "sentiment_score": sentiment,
                    "data_points": {
                        "platform": platform,
                        "likes": post.get("likes", 0),
                        "comments": post.get("comments", 0),
                        "post_text": text
                    }
                })
                
    return {"insights_to_save": insights}

def save_insights(state: AgentState) -> Dict[str, Any]:
    insights = state["insights_to_save"]
    comp_id = state["competitor_id"]
    company_id = state["company_id"]
    
    if not insights:
        return {}
        
    db = SessionLocal()
    try:
        for ins in insights:
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
        db.commit()
        logger.info(f"Saved {len(insights)} social insights to DB for competitor {comp_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving social insights to DB: {e}")
    finally:
        db.close()
        
    return {}

# Define LangGraph graph
workflow = StateGraph(AgentState)

workflow.add_node("detect_platforms", detect_platforms)
workflow.add_node("gather_social", gather_social_data)
workflow.add_node("generate_insights", generate_insights)
workflow.add_node("save_insights", save_insights)

workflow.set_entry_point("detect_platforms")
workflow.add_edge("detect_platforms", "gather_social")
workflow.add_edge("gather_social", "generate_insights")
workflow.add_edge("generate_insights", "save_insights")
workflow.add_edge("save_insights", END)

run_social_agent = workflow.compile()
