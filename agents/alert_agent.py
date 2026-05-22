import os
import sys
import logging
import json
from typing import TypedDict, Dict, Any
from openai import OpenAI

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from app.db.session import SessionLocal
from app.models.events import CompetitorEvent
from app.models.alerts import Alert

logger = logging.getLogger("alert-agent")

class AlertAgentState(TypedDict):
    event_id: int
    competitor_id: int
    severity: str
    alert_id: int
    reasoning: str

def evaluate_rules(state: AlertAgentState) -> Dict[str, Any]:
    event_id = state["event_id"]
    logger.info(f"[AlertAgent - Node: evaluate_rules] Evaluating event {event_id}")
    
    db = SessionLocal()
    try:
        event = db.query(CompetitorEvent).filter(CompetitorEvent.id == event_id).first()
        if not event:
            logger.error(f"Event {event_id} not found in DB.")
            return {"severity": "low", "reasoning": "Event not found."}
        
        competitor_id = event.competitor_id
        
        # Check for OpenAI key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            prompt = f"""
            You are a senior competitor intelligence analyst. Classify the severity of the following competitor event.
            
            EVENT TITLE: {event.title}
            EVENT TYPE: {event.event_type}
            DESCRIPTION: {event.description}
            
            Classify the severity into one of: "high", "medium", "low".
            
            Guidelines:
            - "high": Critical threat. Direct pricing changes (increases/drops), new competitor product/feature launches, funding rounds, merger/acquisitions, major competitor rebranding or strategy pivots.
            - "medium": Moderate threat. Hiring spikes, executive appointments, standard partner announcements, social media spikes.
            - "low": Minor news, general website tweaks, normal job postings, routine social media.
            
            Provide your response in strict JSON format:
            {{
                "severity": "high" | "medium" | "low",
                "reasoning": "A concise explanation of why this severity was assigned."
            }}
            Do not wrap in markdown ```json blocks.
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional analyst who outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                )
                data = json.loads(response.choices[0].message.content.strip())
                severity = data.get("severity", "low").lower()
                reasoning = data.get("reasoning", "LLM evaluation")
                if severity not in ["high", "medium", "low"]:
                    severity = "low"
                return {"severity": severity, "reasoning": reasoning, "competitor_id": competitor_id}
            except Exception as llm_err:
                logger.error(f"LLM severity evaluation failed: {llm_err}. Using rule-based fallback.")
                
        # Rule-based fallback
        severity = "low"
        reasoning = "Rule-based fallback evaluation."
        
        title_lower = event.title.lower() if event.title else ""
        desc_lower = event.description.lower() if event.description else ""
        event_type = event.event_type.lower() if event.event_type else ""
        
        if event_type == "pricing":
            severity = "high"
            reasoning = "Pricing events are classified as high severity."
        elif event_type == "anomaly":
            severity = "high"
            reasoning = "Statistical anomalies are classified as high severity."
        elif event_type == "product" or "launch" in title_lower or "launch" in desc_lower:
            severity = "high"
            reasoning = "Product launches or major feature updates are high severity."
        elif "funding" in title_lower or "acquisition" in title_lower or "acquire" in title_lower:
            severity = "high"
            reasoning = "Funding or acquisition events are high severity."
        elif event_type == "hiring" or "hire" in title_lower or "hiring" in title_lower:
            if any(role in title_lower or role in desc_lower for role in ["director", "vp", "executive", "ceo", "cto", "cfo", "head"]):
                severity = "high"
                reasoning = "Executive hiring is high severity."
            else:
                severity = "medium"
                reasoning = "General hiring activity is medium severity."
        elif event_type == "news" or "partnership" in title_lower or "partner" in title_lower:
            severity = "medium"
            reasoning = "News partnerships are medium severity."
        else:
            if "alert" in title_lower or "critical" in title_lower or "spike" in title_lower:
                severity = "medium"
            else:
                severity = "low"
                
        return {"severity": severity, "reasoning": reasoning, "competitor_id": competitor_id}
    finally:
        db.close()

def save_alert(state: AlertAgentState) -> Dict[str, Any]:
    event_id = state["event_id"]
    severity = state["severity"]
    competitor_id = state.get("competitor_id")
    
    db = SessionLocal()
    alert_id = None
    try:
        # Update Event severity
        event = db.query(CompetitorEvent).filter(CompetitorEvent.id == event_id).first()
        if event:
            event.severity = severity
            db.add(event)
            db.flush()
            if not competitor_id:
                competitor_id = event.competitor_id
        
        # If severity is medium or high, check if Alert already exists or create it
        if severity in ["medium", "high"]:
            existing_alert = db.query(Alert).filter(Alert.event_id == event_id).first()
            if not existing_alert:
                alert = Alert(
                    competitor_id=competitor_id,
                    event_id=event_id,
                    is_read=False
                )
                db.add(alert)
                db.flush()
                alert_id = alert.id
                logger.info(f"Created new Alert id={alert_id} for event_id={event_id}")
            else:
                alert_id = existing_alert.id
                logger.info(f"Alert id={alert_id} already exists for event_id={event_id}")
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving alert: {e}")
    finally:
        db.close()
        
    return {"alert_id": alert_id}

def notify_dispatcher(state: AlertAgentState) -> Dict[str, Any]:
    severity = state["severity"]
    alert_id = state.get("alert_id")
    
    if severity == "high" and alert_id:
        logger.info(f"[AlertAgent - Node: notify_dispatcher] Triggering notifications for high-severity alert {alert_id}")
        try:
            from app.services.notifications import dispatch_notifications
            try:
                # Try Celery delay
                dispatch_notifications.delay(alert_id)
                logger.info("Dispatched notifications via Celery task.")
            except Exception as celery_err:
                logger.warning(f"Could not dispatch via Celery: {celery_err}. Invoking synchronously.")
                dispatch_notifications(alert_id)
        except Exception as e:
            logger.error(f"Error in notify_dispatcher: {e}")
    else:
        logger.info(f"[AlertAgent - Node: notify_dispatcher] Skipping notification for severity={severity}, alert_id={alert_id}")
        
    return {}

workflow = StateGraph(AlertAgentState)
workflow.add_node("evaluate_rules", evaluate_rules)
workflow.add_node("save_alert", save_alert)
workflow.add_node("notify_dispatcher", notify_dispatcher)

workflow.set_entry_point("evaluate_rules")
workflow.add_edge("evaluate_rules", "save_alert")
workflow.add_edge("save_alert", "notify_dispatcher")
workflow.add_edge("notify_dispatcher", END)

alert_workflow = workflow.compile()

def run_alert_agent(event_id: int):
    """
    Executes the Alert Agent workflow on a specific competitor event.
    """
    initial_state = {
        "event_id": event_id,
        "competitor_id": 0,
        "severity": "low",
        "alert_id": None,
        "reasoning": ""
    }
    logger.info(f"Running Alert Agent for event {event_id}")
    return alert_workflow.invoke(initial_state)
