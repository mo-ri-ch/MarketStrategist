import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from openai import OpenAI
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal
from app.models.events import CompetitorEvent
from app.models.prediction import CompetitorPrediction

logger = logging.getLogger("predictor-engine")

def generate_predictions(competitor_id: int, db: Session = None) -> Dict[str, Any]:
    """
    Analyzes competitor's recent events and generates a forecast for their next probable action.
    Saves or updates the record in competitor_predictions.
    """
    is_local_db = False
    if db is None:
        db = SessionLocal()
        is_local_db = True
        
    try:
        # Fetch events for the competitor in the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        events = db.query(CompetitorEvent).filter(
            CompetitorEvent.competitor_id == competitor_id,
            CompetitorEvent.created_at >= thirty_days_ago
        ).order_by(CompetitorEvent.created_at.desc()).all()
        
        # If no events in the last 30 days, get the 5 most recent events overall
        if not events:
            events = db.query(CompetitorEvent).filter(
                CompetitorEvent.competitor_id == competitor_id
            ).order_by(CompetitorEvent.created_at.desc()).limit(5).all()
            
        # Extract basic event data for prompt or heuristics
        event_logs = []
        for e in events:
            event_logs.append({
                "id": e.id,
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "severity": e.severity,
                "created_at": e.created_at.isoformat() if e.created_at else None
            })
            
        predicted_action = ""
        description = ""
        confidence_score = 0.50
        trigger_events = []
        
        # Check OpenAI key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and event_logs:
            client = OpenAI(api_key=api_key)
            prompt = f"""
            You are a senior market analyst specializing in predictive corporate intelligence.
            Review the following list of recent events detected for a competitor.
            Predict their next probable major strategic move (e.g. "Product Launch", "Pricing Restructuring", "Expansion Campaign", "Executive Hirings", "Strategic Partnership", "Geographical Expansion").
            
            RECENT EVENTS:
            {json.dumps(event_logs, indent=2)}
            
            Provide a forecast including:
            1. "predicted_action": The short name of their next move (keep it 2-5 words).
            2. "description": A detailed paragraph explaining the rationale behind this prediction based on the event patterns.
            3. "confidence_score": A float between 0.0 and 1.0.
            4. "trigger_events": A list of event IDs from the input that directly support this prediction.
            
            Provide your response in strict JSON format:
            {{
                "predicted_action": "...",
                "description": "...",
                "confidence_score": 0.85,
                "trigger_events": [12, 15]
            }}
            Do not wrap in markdown ```json blocks.
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional corporate forecaster who outputs only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                )
                data = json.loads(response.choices[0].message.content.strip())
                predicted_action = data.get("predicted_action", "")
                description = data.get("description", "")
                confidence_score = float(data.get("confidence_score", 0.50))
                trigger_ids = data.get("trigger_events", [])
                
                # Verify trigger events are valid
                trigger_events = [e for e in event_logs if e["id"] in trigger_ids]
            except Exception as llm_err:
                logger.error(f"LLM competitor action forecasting failed: {llm_err}. Falling back to heuristics.")
                
        # Rule-based heuristics fallback
        if not predicted_action:
            if not event_logs:
                predicted_action = "Steady State Operations"
                description = "No recent strategic activities or changes have been registered for this competitor. They are likely operating in their standard business baseline."
                confidence_score = 0.50
                trigger_events = []
            else:
                # Analyze event logs
                hiring_events = [e for e in event_logs if e["event_type"] == "hiring"]
                pricing_events = [e for e in event_logs if e["event_type"] == "pricing" or "price" in e["title"].lower() or "pricing" in e["title"].lower()]
                product_events = [e for e in event_logs if e["event_type"] == "product" or "launch" in e["title"].lower()]
                funding_events = [e for e in event_logs if "funding" in e["title"].lower() or "acquisition" in e["title"].lower()]
                partnership_events = [e for e in event_logs if "partner" in e["title"].lower() or "integrate" in e["title"].lower()]
                anomaly_events = [e for e in event_logs if e["event_type"] == "anomaly"]
                
                if pricing_events:
                    predicted_action = "Pricing Restructuring"
                    trigger_events = pricing_events
                    confidence_score = 0.80
                    description = f"Recent price or plan adjustments (e.g. '{pricing_events[0]['title']}') suggest competitor is optimizing customer yield and restructuring subscription tiers."
                elif product_events:
                    predicted_action = "New Feature / Product Rollout"
                    trigger_events = product_events
                    confidence_score = 0.75
                    description = f"Following website changes indicating product developments (such as '{product_events[0]['title']}'), the competitor is forecasted to announce a new product capability."
                elif hiring_events:
                    executive_hires = [e for e in hiring_events if any(role in e["title"].lower() for role in ["director", "vp", "executive", "head", "lead"])]
                    if executive_hires:
                        predicted_action = "Leadership & Strategy Realignment"
                        trigger_events = executive_hires
                        confidence_score = 0.70
                        description = f"Recent high-profile hires (such as '{executive_hires[0]['title']}') point to an impending restructuring of strategy, product roadmap, or team organization."
                    else:
                        predicted_action = "Product Development Surge"
                        trigger_events = hiring_events
                        confidence_score = 0.65
                        description = f"Multiple new developer and engineer job postings suggest competitor is actively scaling up their technical capacity to build new features."
                elif funding_events:
                    predicted_action = "Aggressive Market Expansion"
                    trigger_events = funding_events
                    confidence_score = 0.85
                    description = f"Capital event or restructuring ('{funding_events[0]['title']}') gives the competitor financial leverage to launch new marketing drives or hire aggressively."
                elif partnership_events:
                    predicted_action = "Ecosystem Integration Campaign"
                    trigger_events = partnership_events
                    confidence_score = 0.70
                    description = f"Strategic alliance or integration activity (e.g. '{partnership_events[0]['title']}') indicates competitor is expanding their product compatibility and market reach."
                elif anomaly_events:
                    predicted_action = "Operational Scale-Up"
                    trigger_events = anomaly_events
                    confidence_score = 0.70
                    description = f"A statistical anomaly spike in activities ('{anomaly_events[0]['title']}') suggests sudden operational speed-up or major shifts within their team."
                else:
                    predicted_action = "Incremental Product Optimizations"
                    trigger_events = [event_logs[0]]
                    confidence_score = 0.60
                    description = f"General updates (such as '{event_logs[0]['title']}') suggest standard iterative optimizations without high-risk strategic moves."
                    
        # Upsert into database
        prediction = db.query(CompetitorPrediction).filter(
            CompetitorPrediction.competitor_id == competitor_id
        ).first()
        
        if prediction:
            prediction.predicted_action = predicted_action
            prediction.description = description
            prediction.confidence_score = confidence_score
            prediction.trigger_events = trigger_events
            prediction.updated_at = datetime.utcnow()
            logger.info(f"Updated competitor prediction for competitor_id={competitor_id}")
        else:
            prediction = CompetitorPrediction(
                competitor_id=competitor_id,
                predicted_action=predicted_action,
                description=description,
                confidence_score=confidence_score,
                trigger_events=trigger_events
            )
            db.add(prediction)
            logger.info(f"Created new competitor prediction for competitor_id={competitor_id}")
            
        db.commit()
        
        return {
            "id": prediction.id,
            "competitor_id": competitor_id,
            "predicted_action": predicted_action,
            "description": description,
            "confidence_score": confidence_score,
            "trigger_events": trigger_events,
            "updated_at": prediction.updated_at.isoformat() if prediction.updated_at else datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        if is_local_db:
            db.rollback()
        logger.error(f"Error generating competitor predictions: {e}")
        raise e
    finally:
        if is_local_db:
            db.close()
