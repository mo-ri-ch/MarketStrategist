import os
import sys
import logging
from typing import TypedDict, List, Dict, Any

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.insights import Insight
from app.services.search_trends import discover_unmanaged_competitors

logger = logging.getLogger("market-research-agent")

class AgentState(TypedDict):
    company_id: int
    company_name: str
    company_industry: str
    company_services: str
    company_region: str
    discovered_competitors: List[Dict[str, Any]]
    insights_to_save: List[Dict[str, Any]]

def fetch_company_profile(state: AgentState) -> Dict[str, Any]:
    company_id = state["company_id"]
    logger.info(f"[Node: Fetch Company Profile] Looking up company {company_id}")
    
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return {"company_name": "", "company_industry": "", "company_services": "", "company_region": "Global"}
        return {
            "company_name": company.name,
            "company_industry": company.industry or "Technology",
            "company_services": company.services or "",
            "company_region": company.region or "Global"
        }
    finally:
        db.close()

def run_discovery(state: AgentState) -> Dict[str, Any]:
    name = state["company_name"]
    industry = state["company_industry"]
    services = state["company_services"]
    region = state.get("company_region", "Global")
    
    logger.info(f"[Node: Run Discovery] Finding competitor matches for {name} in region {region}")
    try:
        matches = discover_unmanaged_competitors(name, industry, services, region=region)
        return {"discovered_competitors": matches}
    except Exception as e:
        logger.error(f"Error in run_discovery node: {e}")
        return {"discovered_competitors": []}

def synthesize_market_insights(state: AgentState) -> Dict[str, Any]:
    matches = state["discovered_competitors"]
    logger.info(f"[Node: Synthesize Insights] Transforming {len(matches)} matches into market insights")
    
    insights = []
    for match in matches:
        comp_name = match.get("name", "Unknown")
        website = match.get("website", "")
        desc = match.get("description", "")
        reason = match.get("match_reason", "")
        conf = match.get("confidence_score", 0.8)
        
        insights.append({
            "insight_type": "market",
            "title": f"Discovered Competitor: {comp_name}",
            "description": f"{desc} | Why they compete: {reason}",
            "sentiment_score": -round(conf, 2),  # Higher threat (confidence) could mean negative threat to us
            "data_points": {
                "name": comp_name,
                "website": website,
                "match_reason": reason,
                "confidence_score": conf,
                "is_discovered": True
            }
        })
        
    return {"insights_to_save": insights}

def save_market_insights(state: AgentState) -> Dict[str, Any]:
    insights = state["insights_to_save"]
    company_id = state["company_id"]
    
    if not insights:
        logger.info("No market insights to save.")
        return {}
        
    db = SessionLocal()
    try:
        # Avoid duplicating existing discovered insights
        for ins in insights:
            comp_name = ins["data_points"].get("name")
            
            # Check if this competitor is already actively tracked
            from app.models.competitor import Competitor
            existing_comp = db.query(Competitor).filter(
                Competitor.company_id == company_id,
                Competitor.name == comp_name
            ).first()
            if existing_comp:
                logger.info(f"Competitor {comp_name} is already actively tracked, skipping discovery insight.")
                continue
                
            # Check if this exact discovery insight has already been logged to avoid spamming
            existing_insight = db.query(Insight).filter(
                Insight.company_id == company_id,
                Insight.insight_type == "market",
                Insight.title == ins["title"]
            ).first()
            if existing_insight:
                logger.info(f"Market research discovery insight for {comp_name} already exists, skipping.")
                continue
            
            db_insight = Insight(
                company_id=company_id,
                competitor_id=None,  # Null since they are not yet actively tracked
                insight_type=ins["insight_type"],
                title=ins["title"],
                description=ins["description"],
                sentiment_score=ins["sentiment_score"],
                data_points=ins["data_points"]
            )
            db.add(db_insight)
            
        db.commit()
        logger.info(f"Saved market discovery insights to DB for company {company_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving market insights to DB: {e}")
    finally:
        db.close()
        
    return {}

# Define LangGraph graph
workflow = StateGraph(AgentState)

workflow.add_node("fetch_company", fetch_company_profile)
workflow.add_node("run_discovery", run_discovery)
workflow.add_node("synthesize_insights", synthesize_market_insights)
workflow.add_node("save_insights", save_market_insights)

workflow.set_entry_point("fetch_company")
workflow.add_edge("fetch_company", "run_discovery")
workflow.add_edge("run_discovery", "synthesize_insights")
workflow.add_edge("synthesize_insights", "save_insights")
workflow.add_edge("save_insights", END)

run_market_research_agent = workflow.compile()
