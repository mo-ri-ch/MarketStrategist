import os
import sys
import logging
import json
import re
from typing import TypedDict, List, Dict, Any

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from openai import OpenAI
from app.db.session import SessionLocal
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.alerts import Alert
from app.workers.tasks.scraper import scrape_website

logger = logging.getLogger("website-monitor-agent")

class AgentState(TypedDict):
    competitor_id: int
    url: str
    current_text: str
    previous_text: str
    detected_events: List[Dict[str, Any]]

def fetch_current_content(state: AgentState) -> Dict[str, Any]:
    url = state["url"]
    logger.info(f"[Node: Fetch Current] Scraping {url}")
    try:
        text = scrape_website(url)
        return {"current_text": text}
    except Exception as e:
        logger.error(f"Error in fetch_current_content node: {e}")
        return {"current_text": ""}

def fetch_previous_content(state: AgentState) -> Dict[str, Any]:
    comp_id = state["competitor_id"]
    logger.info(f"[Node: Fetch Previous] Reading cache for competitor {comp_id}")
    
    # Cache directory for raw scrapes
    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "storage", "scrapes"))
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{comp_id}.txt")
    
    previous_text = ""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                previous_text = f.read()
        except Exception as e:
            logger.error(f"Failed to read cache file: {e}")
            
    return {"previous_text": previous_text}

def analyze_diff(state: AgentState) -> Dict[str, Any]:
    current = state["current_text"]
    previous = state["previous_text"]
    comp_id = state["competitor_id"]
    
    if not current:
        logger.warning("No current text to analyze.")
        return {"detected_events": []}
        
    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "storage", "scrapes"))
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{comp_id}.txt")

    # If no previous scrape, register baseline
    if not previous:
        logger.info("No previous crawl history found. Registering baseline event.")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(current)
        except Exception as e:
            logger.error(f"Failed to save current content to cache: {e}")
            
        return {
            "detected_events": [{
                "event_type": "general",
                "title": "Baseline Crawl Complete",
                "description": "Established first baseline tracking dataset. Scraper is active.",
                "original_text_diff": None,
                "confidence_score": 1.0,
                "severity": "low"
            }]
        }
        
    if current == previous:
        logger.info("No text changes detected between scrapes.")
        return {"detected_events": []}
        
    # We have a diff. Check for OpenAI key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found. Simulating changes in mock diff.")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(current)
        except Exception as e:
            logger.error(f"Failed to save current content to cache: {e}")
            
        return {
            "detected_events": [{
                "event_type": "product",
                "title": "Website Modification Detected",
                "description": "The target website has updated its landing text. (API key not set, details mocked)",
                "original_text_diff": "Change in content layout detected.",
                "confidence_score": 0.8,
                "severity": "medium"
            }]
        }
        
    # Call OpenAI to parse structural difference
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an expert strategic analyst. Compare the PREVIOUS website text with the CURRENT website text of a competitor.
    Identify any meaningful changes. Ignore minor formatting shifts, header/footer changes, or copyright year updates.
    Focus on strategic shifts:
    - Pricing / Plans changes
    - New feature or product announcements
    - Key job postings or hiring surges
    - Major client or partner logos added
    - Value proposition changes

    PREVIOUS TEXT (truncated if long):
    {previous[:8000]}

    CURRENT TEXT (truncated if long):
    {current[:8000]}

    Provide your output as a valid JSON list of event objects. Each object must have these exact fields:
    - "event_type": "pricing" | "product" | "hiring" | "general"
    - "title": A short header summarizing the change
    - "description": 1-2 sentences explaining what changed and the business implication
    - "severity": "low" | "medium" | "high"
    - "confidence_score": Float between 0.0 and 1.0 indicating your certainty.

    If no strategic changes are found, return an empty JSON list: [].
    Ensure your output is strictly valid JSON starting with [ and ending with ]. Do not wrap in markdown ```json blocks.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional corporate intelligence analyst who outputs only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            events = json.loads(content)
            if not isinstance(events, list):
                events = []
        except Exception as json_err:
            logger.error(f"Failed to parse JSON from LLM response: {json_err}. Raw content: {content}")
            events = []
            
        # Update cache
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(current)
            
        return {"detected_events": events}
    except Exception as e:
        logger.error(f"Error in analyze_diff node: {e}")
        return {"detected_events": []}

def save_events(state: AgentState) -> Dict[str, Any]:
    events = state["detected_events"]
    comp_id = state["competitor_id"]
    
    if not events:
        logger.info("No events to save to DB.")
        return {}
        
    db = SessionLocal()
    saved_event_ids = []
    try:
        competitor = db.query(Competitor).filter(Competitor.id == comp_id).first()
        region = competitor.region if competitor else "Global"
        for event in events:
            db_event = CompetitorEvent(
                competitor_id=comp_id,
                event_type=event.get("event_type", "general"),
                title=event.get("title", "Website Update"),
                description=event.get("description", "A change was discovered on the target's website."),
                original_text_diff=event.get("original_text_diff"),
                confidence_score=event.get("confidence_score", 1.0),
                severity="low",  # Default to low, let Alert Agent evaluate
                region=region
            )
            db.add(db_event)
            db.flush()
            saved_event_ids.append(db_event.id)

        db.commit()
        logger.info(f"Saved {len(events)} events to database for competitor {comp_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving events to DB: {e}")
        saved_event_ids = []
    finally:
        db.close()
        
    # Trigger Alert Agent for each saved event
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from alert_agent import run_alert_agent
    for ev_id in saved_event_ids:
        try:
            logger.info(f"Triggering Alert Agent workflow for event {ev_id}")
            run_alert_agent(ev_id)
        except Exception as ae:
            logger.error(f"Failed to run Alert Agent on event {ev_id}: {ae}")
        
    return {}

# Define LangGraph graph
workflow = StateGraph(AgentState)

workflow.add_node("fetch_current", fetch_current_content)
workflow.add_node("fetch_previous", fetch_previous_content)
workflow.add_node("analyze_diff", analyze_diff)
workflow.add_node("save_events", save_events)

workflow.set_entry_point("fetch_current")

workflow.add_conditional_edges(
    "fetch_current",
    lambda state: "continue" if state["current_text"] else "end",
    {
        "continue": "fetch_previous",
        "end": END
    }
)

workflow.add_edge("fetch_previous", "analyze_diff")
workflow.add_edge("analyze_diff", "save_events")
workflow.add_edge("save_events", END)

run_monitor_agent = workflow.compile()
