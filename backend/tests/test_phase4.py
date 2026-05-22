import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Add backend and parent directories to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure Celery for in-memory / eager execution BEFORE importing models/tasks
from app.workers.celery_app import celery_app
celery_app.conf.update(
    broker_url='memory://',
    result_backend=None,
    task_always_eager=True,
    task_eager_propagates=True,
)

from app.models.base import Base
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.alerts import Alert
from app.models.prediction import CompetitorPrediction

class TestPhase4Suite(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)
        
        # Override SessionLocal inside session module BEFORE other imports
        import app.db.session
        self.original_session_local = app.db.session.SessionLocal
        app.db.session.SessionLocal = self.TestingSessionLocal
        
        # Import services and agents
        import agents.alert_agent
        # Alias in sys.modules to prevent double-import mismatches (alert_agent vs agents.alert_agent)
        sys.modules["alert_agent"] = agents.alert_agent
        
        import app.services.notifications
        import app.services.anomaly_detector
        import app.services.predictor
        
        # Inject testing session local
        agents.alert_agent.SessionLocal = self.TestingSessionLocal
        app.services.notifications.SessionLocal = self.TestingSessionLocal
        app.services.anomaly_detector.SessionLocal = self.TestingSessionLocal
        app.services.predictor.SessionLocal = self.TestingSessionLocal
        
        self.db = self.TestingSessionLocal()
        
        # Seed test user
        self.user = User(
            id=1,
            email="owner@test.com",
            hashed_password="fakepassword",
            full_name="Owner Admin",
            role="admin",
            is_active=True
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        # Seed company
        self.company = Company(
            id=1,
            name="Target Corp",
            website="https://target.com",
            user_id=self.user.id,
            notification_email="alerts@target.com",
            webhook_url="https://api.target.com/webhook"
        )
        self.db.add(self.company)
        self.db.commit()
        self.db.refresh(self.company)
        
        # Seed competitor
        self.competitor = Competitor(
            id=1,
            company_id=self.company.id,
            name="Competitor One",
            website="https://competitor1.com"
        )
        self.db.add(self.competitor)
        self.db.commit()
        self.db.refresh(self.competitor)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        import app.db.session
        app.db.session.SessionLocal = self.original_session_local

    def test_alert_agent_severity_and_alert_creation(self):
        """
        Verify that Alert Agent correctly classifies pricing and anomaly events,
        saves their severity to the DB, and registers Alert records.
        """
        from agents.alert_agent import run_alert_agent
        
        # 1. Test high-severity rule (pricing event)
        pricing_event = CompetitorEvent(
            id=101,
            competitor_id=self.competitor.id,
            event_type="pricing",
            title="Premium tier price reduction by 20%",
            description="Competitor dropped price from $100 to $80.",
            confidence_score=0.95,
            severity="low" # will be evaluated and updated
        )
        self.db.add(pricing_event)
        self.db.commit()
        
        # Run alert agent
        with patch("app.services.notifications.dispatch_notifications") as mock_dispatch:
            run_alert_agent(pricing_event.id)
            
            # Re-fetch event and verify severity updated to high
            self.db.refresh(pricing_event)
            self.assertEqual(pricing_event.severity, "high")
            
            # Verify alert created in DB
            alert = self.db.query(Alert).filter(Alert.event_id == pricing_event.id).first()
            self.assertIsNotNone(alert)
            self.assertEqual(alert.competitor_id, self.competitor.id)
            
            # Verify notifications dispatched via Celery task .delay() method
            mock_dispatch.delay.assert_called_once_with(alert.id)

    def test_notification_dispatcher_fallback_file(self):
        """
        Verify that send_alert_email writes HTML outputs to local storage when SMTP is missing.
        """
        from app.services.notifications import send_alert_email
        
        event = CompetitorEvent(
            id=201,
            competitor_id=self.competitor.id,
            event_type="product",
            title="Competitor launched feature X",
            description="A new dashboard features was released.",
            confidence_score=0.88,
            severity="high"
        )
        self.db.add(event)
        self.db.commit()
        
        alert = Alert(
            id=501,
            competitor_id=self.competitor.id,
            event_id=event.id,
            is_read=False
        )
        self.db.add(alert)
        self.db.commit()
        
        # Call dispatcher
        with patch.dict(os.environ, {}, clear=True):
            send_alert_email(alert.id)
            
            # Email fallback output directory check (in app/storage/emails)
            email_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "storage", "emails"))
            self.assertTrue(os.path.exists(email_dir))
            
            # Verify a file starts with alert_501_
            files = os.listdir(email_dir)
            matching_files = [f for f in files if f.startswith("alert_501_")]
            self.assertTrue(len(matching_files) > 0)
            
            # Read one file to verify HTML contents
            file_path = os.path.join(email_dir, matching_files[0])
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Competitor launched feature X", content)
            
            # Clean up test output
            os.remove(file_path)

    @patch("httpx.Client.post")
    def test_webhook_dispatcher_delivers_payload(self, mock_post):
        """
        Verify webhook post sends correct payload to company's webhook_url.
        """
        from app.services.notifications import send_alert_webhook
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        event = CompetitorEvent(
            id=301,
            competitor_id=self.competitor.id,
            event_type="pricing",
            title="Slight increase",
            description="Up by 5%",
            confidence_score=0.90,
            severity="high"
        )
        self.db.add(event)
        
        alert = Alert(
            id=601,
            competitor_id=self.competitor.id,
            event_id=event.id
        )
        self.db.add(alert)
        self.db.commit()
        
        send_alert_webhook(alert.id)
        
        # Verify post called with URL and JSON payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.target.com/webhook")
        self.assertEqual(kwargs["json"]["alert_id"], 601)
        self.assertEqual(kwargs["json"]["company_name"], "Target Corp")

    def test_anomaly_detector_spikes(self):
        """
        Verify that 30-day baseline comparisons successfully trigger anomaly events.
        """
        from app.services.anomaly_detector import detect_competitor_anomalies
        
        # 1. Seed events in the 23-day baseline range (e.g. 2 events overall)
        base_time_1 = datetime.utcnow() - timedelta(days=15)
        base_time_2 = datetime.utcnow() - timedelta(days=20)
        
        e1 = CompetitorEvent(
            competitor_id=self.competitor.id,
            event_type="hiring",
            title="Hiring engineer",
            description="Engineering team scaling baseline.",
            created_at=base_time_1
        )
        e2 = CompetitorEvent(
            competitor_id=self.competitor.id,
            event_type="hiring",
            title="Hiring designer",
            description="Design team scaling baseline.",
            created_at=base_time_2
        )
        self.db.add(e1)
        self.db.add(e2)
        
        # 2. Seed a burst of 5 events in the current week (7 days)
        for i in range(5):
            curr_event = CompetitorEvent(
                competitor_id=self.competitor.id,
                event_type="hiring",
                title=f"Hiring developer {i}",
                description="Hiring new engineer to build software features.",
                created_at=datetime.utcnow() - timedelta(hours=i*2)
            )
            self.db.add(curr_event)
            
        self.db.commit()
        
        # Run anomaly detection
        with patch("agents.alert_agent.run_alert_agent") as mock_run_agent:
            anomalies = detect_competitor_anomalies(self.company.id, self.db)
            
            # Anomaly event should be created and returned
            self.assertTrue(len(anomalies) > 0)
            
            # Check DB to verify anomaly event details
            anomaly_event = self.db.query(CompetitorEvent).filter(
                CompetitorEvent.event_type == "anomaly",
                CompetitorEvent.competitor_id == self.competitor.id,
                CompetitorEvent.title.like("%Hiring%")
            ).first()
            self.assertIsNotNone(anomaly_event)
            self.assertIn("Hiring activity spike detected", anomaly_event.title)
            
            # Verify Alert Agent was triggered for this anomaly event
            mock_run_agent.assert_any_call(anomaly_event.id)

    def test_competitor_action_predictor(self):
        """
        Verify competitor action predictor correctly registers forecasting actions.
        """
        from app.services.predictor import generate_predictions
        
        # Seed hiring events for predictor
        e1 = CompetitorEvent(
            competitor_id=self.competitor.id,
            event_type="hiring",
            title="Hiring Director of Engineering",
            description="Scaling engineering leadership team."
        )
        e2 = CompetitorEvent(
            competitor_id=self.competitor.id,
            event_type="hiring",
            title="Hiring VP of Product",
            description="Developing next-gen cloud systems."
        )
        self.db.add(e1)
        self.db.add(e2)
        self.db.commit()
        
        # Mock OpenAI environment as empty to use heuristic rules
        with patch.dict(os.environ, {}, clear=True):
            predictions = generate_predictions(self.competitor.id, self.db)
            
            self.assertIsNotNone(predictions)
            self.assertEqual(predictions["predicted_action"], "Leadership & Strategy Realignment")
            self.assertTrue(predictions["confidence_score"] > 0.5)
            
            # Verify saved prediction record in DB
            db_pred = self.db.query(CompetitorPrediction).filter(
                CompetitorPrediction.competitor_id == self.competitor.id
            ).first()
            self.assertIsNotNone(db_pred)
            self.assertEqual(db_pred.predicted_action, "Leadership & Strategy Realignment")
            self.assertEqual(len(db_pred.trigger_events), 2)

if __name__ == "__main__":
    unittest.main()
