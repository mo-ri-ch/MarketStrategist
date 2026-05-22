import os
import logging
import json
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.alerts import Alert
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.user import User

logger = logging.getLogger("market-strategist-notifications")

def send_alert_email(alert_id: int):
    """
    Constructs and sends an email notification for the alert.
    If SMTP credentials are not set in environment, logs to local storage.
    """
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert id={alert_id} not found for email dispatch.")
            return

        competitor = db.query(Competitor).filter(Competitor.id == alert.competitor_id).first()
        event = db.query(CompetitorEvent).filter(CompetitorEvent.id == alert.event_id).first()
        if not competitor or not event:
            logger.error("Competitor or event not found for alert email dispatch.")
            return

        company = db.query(Company).filter(Company.id == competitor.company_id).first()
        owner = db.query(User).filter(User.id == company.user_id).first() if company else None

        recipient_email = company.notification_email if company and company.notification_email else (owner.email if owner else "admin@marketstrategist.local")
        company_name = company.name if company else "MarketStrategist"

        subject = f"[CRITICAL ALERT] {competitor.name}: {event.title}"
        
        # Email Body (HTML)
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #0d0e12; color: #ffffff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #1a1c23; border: 1px solid #3b82f6; border-radius: 12px; padding: 30px;">
                    <h2 style="color: #f87171; border-bottom: 1px solid #2e303f; padding-bottom: 10px;">Critical Competitor Activity Flagged</h2>
                    <p style="font-size: 14px; color: #9ca3af;">Strategic Alert triggered for <strong>{company_name}</strong>.</p>
                    
                    <div style="background-color: #262936; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <h3 style="margin: 0 0 5px 0; color: #ffffff;">{competitor.name}</h3>
                        <p style="margin: 0; font-size: 14px; font-weight: bold; color: #ef4444;">Type: {event.event_type.upper()} | Severity: {event.severity.upper()}</p>
                    </div>

                    <h4 style="color: #ffffff; margin-bottom: 5px;">{event.title}</h4>
                    <p style="font-size: 14px; color: #d1d5db; line-height: 1.6;">{event.description}</p>
                    
                    <p style="font-size: 12px; color: #6b7280; margin-top: 30px; border-top: 1px solid #2e303f; padding-top: 15px;">
                        Confidence Score: {event.confidence_score:.2f} | Logged At: {event.created_at}
                    </p>
                </div>
            </body>
        </html>
        """

        # SMTP logic or local fallback
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if smtp_server and smtp_port and smtp_user and smtp_password:
            # Real SMTP execution
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipient_email, msg.as_string())
            logger.info(f"Successfully sent alert email to {recipient_email} via SMTP.")
        else:
            # Fallback local log
            email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage", "emails"))
            os.makedirs(email_dir, exist_ok=True)
            email_path = os.path.join(email_dir, f"alert_{alert_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
            with open(email_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"[Mock Notification] Saved alert {alert_id} email to local storage: {email_path}")

    except Exception as e:
        logger.error(f"Error executing email dispatch for alert {alert_id}: {e}")
    finally:
        db.close()


def send_alert_webhook(alert_id: int):
    """
    POSTs the alert JSON payload to the company's webhook_url.
    """
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert id={alert_id} not found for webhook dispatch.")
            return

        competitor = db.query(Competitor).filter(Competitor.id == alert.competitor_id).first()
        event = db.query(CompetitorEvent).filter(CompetitorEvent.id == alert.event_id).first()
        if not competitor or not event:
            logger.error("Competitor or event not found for alert webhook dispatch.")
            return

        company = db.query(Company).filter(Company.id == competitor.company_id).first()
        if not company or not company.webhook_url:
            logger.info(f"No webhook_url configured for company of competitor {competitor.name}. Skipping webhook.")
            return

        payload = {
            "alert_id": alert.id,
            "company_name": company.name,
            "competitor_name": competitor.name,
            "event": {
                "id": event.id,
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "severity": event.severity,
                "confidence_score": event.confidence_score,
                "created_at": event.created_at.isoformat() if event.created_at else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send POST request
        headers = {"Content-Type": "application/json"}
        # Send non-blocking to prevent locking worker
        with httpx.Client() as client:
            response = client.post(company.webhook_url, json=payload, headers=headers, timeout=10.0)
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Webhook delivered successfully to {company.webhook_url} with status {response.status_code}.")
            else:
                logger.warning(f"Webhook returned status {response.status_code} for {company.webhook_url}.")
            
    except Exception as e:
        logger.error(f"Failed to post alert webhook for alert {alert_id}: {e}")
    finally:
        db.close()


# Import Celery app for task execution
from app.workers.celery_app import celery_app

@celery_app.task(name="app.workers.tasks.notifications.dispatch_notifications")
def dispatch_notifications(alert_id: int):
    """
    Celery task: Dispatch email and webhook notifications for an alert.
    Only triggered for high priority/severity alerts.
    """
    logger.info(f"Dispatching notifications for alert {alert_id}")
    send_alert_email(alert_id)
    send_alert_webhook(alert_id)
