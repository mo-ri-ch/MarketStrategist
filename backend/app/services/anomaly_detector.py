import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add backend directory to sys.path to allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent

logger = logging.getLogger("anomaly-detector")

def detect_competitor_anomalies(company_id: int, db: Session = None):
    """
    Computes weekly baseline event frequencies for competitors of a given company.
    If current weekly count represents a statistically significant anomaly,
    creates a CompetitorEvent of type 'anomaly' and triggers Alert Agent.
    """
    is_local_db = False
    if db is None:
        db = SessionLocal()
        is_local_db = True
        
    try:
        # Get all competitors of the company
        competitors = db.query(Competitor).filter(Competitor.company_id == company_id).all()
        if not competitors:
            logger.info(f"No competitors found for company_id={company_id}")
            return []
            
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        anomalies_detected = []
        
        for competitor in competitors:
            # Query events for the competitor in the last 30 days
            events_30d = db.query(CompetitorEvent).filter(
                CompetitorEvent.competitor_id == competitor.id,
                CompetitorEvent.created_at >= thirty_days_ago
            ).all()
            
            if not events_30d:
                continue
                
            # Group events by type to detect anomalies per event type
            event_types = set(e.event_type for e in events_30d)
            event_types.add("all")  # for overall volume anomalies
            
            for etype in event_types:
                if etype == "all":
                    baseline_events = [e for e in events_30d if e.created_at < week_ago]
                    current_events = [e for e in events_30d if e.created_at >= week_ago]
                else:
                    baseline_events = [e for e in events_30d if e.event_type == etype and e.created_at < week_ago]
                    current_events = [e for e in events_30d if e.event_type == etype and e.created_at >= week_ago]
                    
                baseline_count = len(baseline_events)
                current_count = len(current_events)
                
                # Baseline is over 23 days (from day -30 to day -7)
                baseline_weekly_avg = baseline_count / (23.0 / 7.0)
                
                # Threshold for anomaly:
                # 1. At least 3 events in current week
                # 2. Count exceeds baseline weekly average * 2.5
                threshold = max(3.0, baseline_weekly_avg * 2.5)
                
                if current_count >= threshold:
                    title = f"Anomaly: {etype.capitalize()} activity spike detected for {competitor.name}"
                    description = (
                        f"A significant spike in '{etype}' events was detected. "
                        f"There were {current_count} events in the past 7 days, "
                        f"compared to a weekly baseline average of {baseline_weekly_avg:.1f} events "
                        f"over the previous 23 days."
                    )
                    
                    # Prevent duplicate anomaly events of same type created recently (e.g. past 24 hours)
                    recent_anomaly = db.query(CompetitorEvent).filter(
                        CompetitorEvent.competitor_id == competitor.id,
                        CompetitorEvent.event_type == "anomaly",
                        CompetitorEvent.title == title,
                        CompetitorEvent.created_at >= now - timedelta(days=1)
                    ).first()
                    
                    if not recent_anomaly:
                        anomaly_event = CompetitorEvent(
                            competitor_id=competitor.id,
                            event_type="anomaly",
                            title=title,
                            description=description,
                            confidence_score=0.90,
                            severity="low"  # Default to low, Alert Agent will elevate it to high
                        )
                        db.add(anomaly_event)
                        db.flush()
                        anomalies_detected.append(anomaly_event.id)
                        logger.info(f"Anomaly detected and event created for {competitor.name} ({etype})")
                        
        if anomalies_detected:
            db.commit()
            
            # Now run Alert Agent on newly created anomalies
            try:
                agents_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents"))
                if agents_path not in sys.path:
                    sys.path.append(agents_path)
                from alert_agent import run_alert_agent
                for anim_id in anomalies_detected:
                    logger.info(f"Running Alert Agent for anomaly event {anim_id}")
                    run_alert_agent(anim_id)
            except Exception as ae:
                logger.error(f"Failed to run Alert Agent on anomalies: {ae}")
                
        return anomalies_detected
                
    except Exception as e:
        if is_local_db:
            db.rollback()
        logger.error(f"Error in detect_competitor_anomalies: {e}")
        raise e
    finally:
        if is_local_db:
            db.close()
