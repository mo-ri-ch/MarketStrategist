import os
import sys
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Add agents directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.models.base import Base
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.events import CompetitorEvent
from app.models.recommendations import Recommendation

class TestRecommendationAgent(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Create all tables in the SQLite database
        Base.metadata.create_all(bind=self.engine)
        
        # Override SessionLocal in the agent module
        import agents.recommendation as recommendation_agent
        self.original_session_local = recommendation_agent.SessionLocal
        recommendation_agent.SessionLocal = self.TestingSessionLocal
        
        # Create a test session
        self.db = self.TestingSessionLocal()
        
        # Seed test user
        self.user = User(
            email="testuser@example.com",
            hashed_password="fakehashedpassword",
            full_name="Test User",
            role="admin",
            is_active=True
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        
        # Seed test company
        self.company = Company(
            name="Target Company",
            website="https://target.com",
            industry="Software Automation",
            goals="Acquire more enterprise users and improve feature parity.",
            user_id=self.user.id
        )
        self.db.add(self.company)
        self.db.commit()
        self.db.refresh(self.company)
        
        # Seed test competitor
        self.competitor = Competitor(
            company_id=self.company.id,
            name="Competitor X",
            website="https://competitorx.com",
            linkedin_url="https://linkedin.com/company/competitorx"
        )
        self.db.add(self.competitor)
        self.db.commit()
        self.db.refresh(self.competitor)
        
        # Seed a competitor event
        self.event = CompetitorEvent(
            competitor_id=self.competitor.id,
            event_type="pricing",
            title="Competitor X Dropped Starter Prices by 20%",
            description="A change on the pricing page reflects a 20% discount on starter plans.",
            confidence_score=0.9,
            severity="high"
        )
        self.db.add(self.event)
        self.db.commit()
        self.db.refresh(self.event)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        import agents.recommendation as recommendation_agent
        recommendation_agent.SessionLocal = self.original_session_local

    def test_recommendation_agent_workflow(self):
        from agents.recommendation import run_recommendation_agent
        
        # Invoke the LangGraph workflow
        initial_state = {
            "company_id": self.company.id,
            "events_to_analyze": [],
            "recommendations_to_save": []
        }
        
        result = run_recommendation_agent.invoke(initial_state)
        
        # Verify the end state has analyzed events and recommendations
        self.assertTrue(len(result["events_to_analyze"]) > 0)
        self.assertTrue(len(result["recommendations_to_save"]) > 0)
        
        # Verify recommendations were saved to the database
        db_recs = self.db.query(Recommendation).filter(
            Recommendation.company_id == self.company.id
        ).all()
        
        self.assertTrue(len(db_recs) > 0)
        rec = db_recs[0]
        self.assertEqual(rec.trigger_event_id, self.event.id)
        self.assertIn("Pricing", rec.title)
        self.assertEqual(rec.priority, "high")
        self.assertEqual(rec.status, "pending")
        
        print(f"Verified recommendation agent. Saved {len(db_recs)} strategic recommendations successfully.")

if __name__ == "__main__":
    unittest.main()
