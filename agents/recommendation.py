import os
import sys
import logging
import json
from typing import TypedDict, List, Dict, Any
from datetime import datetime, timedelta

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from openai import OpenAI
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.insights import Insight
from app.models.recommendations import Recommendation

logger = logging.getLogger("recommendation-agent")

class AgentState(TypedDict):
    company_id: int
    events_to_analyze: List[Dict[str, Any]]
    recommendations_to_save: List[Dict[str, Any]]

def fetch_events_and_insights(state: AgentState) -> Dict[str, Any]:
    company_id = state["company_id"]
    logger.info(f"[Node: Fetch Events] Finding events needing recommendations for company {company_id}")
    
    db = SessionLocal()
    try:
        # Get all competitors linked to this company
        competitors = db.query(Competitor).filter(Competitor.company_id == company_id).all()
        comp_ids = [c.id for c in competitors]
        
        if not comp_ids:
            return {"events_to_analyze": []}
            
        # Find competitor events that do NOT have a recommendation linked to them
        # Let's check which events already have recommendations
        existing_rec_event_ids = [
            r.trigger_event_id 
            for r in db.query(Recommendation).filter(
                Recommendation.company_id == company_id,
                Recommendation.trigger_event_id.isnot(None)
            ).all()
        ]
        
        unresolved_events = db.query(CompetitorEvent).filter(
            CompetitorEvent.competitor_id.in_(comp_ids),
            CompetitorEvent.id.not_in(existing_rec_event_ids) if existing_rec_event_ids else True
        ).all()
        
        events_data = []
        for ev in unresolved_events:
            events_data.append({
                "id": ev.id,
                "competitor_id": ev.competitor_id,
                "competitor_name": ev.competitor.name,
                "event_type": ev.event_type,
                "title": ev.title,
                "description": ev.description,
                "severity": ev.severity
            })
            
        logger.info(f"Found {len(events_data)} unresolved events to analyze.")
        return {"events_to_analyze": events_data}
    finally:
        db.close()

def generate_recommendations(state: AgentState) -> Dict[str, Any]:
    events = state["events_to_analyze"]
    company_id = state["company_id"]
    
    if not events:
        logger.info("No events to analyze. Generating general strategy recommendation based on company goals.")
        return {"recommendations_to_save": []}
        
    db = SessionLocal()
    company_name = ""
    company_industry = ""
    company_goals = ""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company_name = company.name
            company_industry = company.industry
            company_goals = company.goals
    finally:
        db.close()
        
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("OPENAI_API_KEY not set. Using rule-based recommendation generator.")
        recommendations = []
        for ev in events:
            ev_type = ev.get("event_type", "general")
            desc = ev.get("description", "")
            comp_name = ev.get("competitor_name", "a competitor")
            ev_id = ev.get("id")
            
            if ev_type == "pricing":
                rec = {
                    "trigger_event_id": ev_id,
                    "title": f"Defensive Pricing Response - {comp_name}",
                    "strategic_action": "Conduct a customer tier pricing audit. Formulate a temporary loyalty discount or refine the features offered in the starter plan to reduce churn risk.",
                    "rationale": f"Competitor {comp_name} adjusted their prices: '{desc}'. High potential for price-sensitive user churn.",
                    "priority": "high" if ev.get("severity") == "high" else "medium"
                }
            elif ev_type == "product":
                rec = {
                    "trigger_event_id": ev_id,
                    "title": f"Feature Gap Mitigation - {comp_name}",
                    "strategic_action": "Task the product management team to review the competitor's release. Assess if these new features can be matched or rendered obsolete by launching planned roadmap capabilities.",
                    "rationale": f"Competitor {comp_name} announced new product offerings: '{desc}'. Essential to prevent technology gap widening.",
                    "priority": "high" if ev.get("severity") == "high" else "medium"
                }
            elif ev_type == "hiring":
                rec = {
                    "trigger_event_id": ev_id,
                    "title": f"Talent Retention & Hiring Alignment",
                    "strategic_action": "Review key engineering and sales compensation structures. Check if hiring pipeline in similar regions needs acceleration to offset competitor expansion.",
                    "rationale": f"Competitor {comp_name} shows significant hiring updates: '{desc}'. Indicates growth acceleration in technical or business development teams.",
                    "priority": "medium"
                }
            elif ev_type == "news":
                rec = {
                    "trigger_event_id": ev_id,
                    "title": f"Strategic Response: {comp_name} News Update",
                    "strategic_action": "Initiate a competitor capability review. Assess whether their recent partnerships or capital expansion requires a revised marketing campaign focusing on our core strengths.",
                    "rationale": f"Critical news event detected for {comp_name}: '{desc}'. Indicates potential changes in their scale or market reach.",
                    "priority": "high" if ev.get("severity") == "high" else "medium"
                }
            else:
                rec = {
                    "trigger_event_id": ev_id,
                    "title": f"Strategic Alert Response - {comp_name}",
                    "strategic_action": "Monitor user feedback and industry channels. Verify if competitor's updates are gaining positive traction with clients.",
                    "rationale": f"An event was detected for {comp_name}: '{desc}'.",
                    "priority": "low"
                }
            recommendations.append(rec)
            
        return {"recommendations_to_save": recommendations}
        
    client = OpenAI(api_key=api_key)
    
    # Prompt OpenAI to analyze events and output recommendations
    prompt = f"""
    You are the Chief AI Strategist for "{company_name}", which operates in the "{company_industry or 'Technology'}" sector.
    The company's primary strategic goals are: "{company_goals or 'Market growth and customer retention'}".
    
    Here is a list of recent competitor events that have been flagged:
    {json.dumps(events, indent=2)}
    
    For each event, formulate an actionable, high-quality strategic recommendation for the CEO.
    Ensure recommendations are specific to the type of threat.
    
    Provide the output strictly as a valid JSON list. Each object must have these exact fields:
    - "trigger_event_id": The exact integer ID of the event that triggered this recommendation (from the event object)
    - "title": A professional, strategic title for the recommendation (e.g. "Counter Pricing Campaign against Competitor X")
    - "strategic_action": 2-3 sentences outlining the exact operational action to take.
    - "rationale": 2-3 sentences explaining the tactical business reasoning behind this choice.
    - "priority": "low" | "medium" | "high" (based on severity and threat impact)
    
    Strictly valid JSON starting with [ and ending with ]. No markdown wrappers.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional board-level strategic advisor and chief of staff who outputs only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:]
            else:
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
        recs = json.loads(content)
        return {"recommendations_to_save": recs}
    except Exception as e:
        logger.error(f"Error calling OpenAI in recommendation generator: {e}")
        return {"recommendations_to_save": []}

def save_recommendations(state: AgentState) -> Dict[str, Any]:
    recs = state["recommendations_to_save"]
    company_id = state["company_id"]
    
    if not recs:
        logger.info("No recommendations to save to DB.")
        return {}
        
    db = SessionLocal()
    try:
        for rec in recs:
            db_rec = Recommendation(
                company_id=company_id,
                trigger_event_id=rec.get("trigger_event_id"),
                title=rec["title"],
                strategic_action=rec["strategic_action"],
                rationale=rec["rationale"],
                priority=rec.get("priority", "medium"),
                status="pending"
            )
            db.add(db_rec)
        db.commit()
        logger.info(f"Saved {len(recs)} strategic recommendations to DB for company {company_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving recommendations to DB: {e}")
    finally:
        db.close()
        
    return {}

# Define LangGraph graph
workflow = StateGraph(AgentState)

workflow.add_node("fetch_events", fetch_events_and_insights)
workflow.add_node("generate_recs", generate_recommendations)
workflow.add_node("save_recs", save_recommendations)

workflow.set_entry_point("fetch_events")
workflow.add_edge("fetch_events", "generate_recs")
workflow.add_edge("generate_recs", "save_recs")
workflow.add_edge("save_recs", END)

run_recommendation_agent = workflow.compile()
