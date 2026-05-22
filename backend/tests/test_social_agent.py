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
from app.models.insights import Insight

class TestSocialIntelligenceAgent(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Create all tables in the SQLite database
        Base.metadata.create_all(bind=self.engine)
        
        # Override SessionLocal in the agent module
        import agents.social_intelligence as social_agent
        self.original_session_local = social_agent.SessionLocal
        social_agent.SessionLocal = self.TestingSessionLocal
        
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
            industry="Technology",
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

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        import agents.social_intelligence as social_agent
        social_agent.SessionLocal = self.original_session_local

    def test_social_agent_workflow(self):
        from agents.social_intelligence import run_social_agent
        
        # Invoke the LangGraph workflow
        initial_state = {
            "competitor_id": self.competitor.id,
            "company_id": self.company.id,
            "competitor_name": self.competitor.name,
            "active_platforms": [],
            "scraped_data": {},
            "insights_to_save": []
        }
        
        result = run_social_agent.invoke(initial_state)
        
        # Verify the end state has scraped platforms
        self.assertIn("linkedin", result["active_platforms"])
        self.assertTrue(len(result["scraped_data"]) > 0)
        self.assertTrue(len(result["insights_to_save"]) > 0)
        
        # Verify insights were saved to the database
        db_insights = self.db.query(Insight).filter(Insight.competitor_id == self.competitor.id).all()
        self.assertTrue(len(db_insights) > 0)
        
        # Check specific platform insight attributes
        linkedin_insight = next(
            (ins for ins in db_insights if ins.data_points.get("platform") == "linkedin"), 
            None
        )
        self.assertIsNotNone(linkedin_insight)
        self.assertEqual(linkedin_insight.insight_type, "social")
        self.assertIn("Presence Summary", linkedin_insight.title)
        self.assertTrue(linkedin_insight.sentiment_score >= -1.0 and linkedin_insight.sentiment_score <= 1.0)
        
        print(f"Verified social intelligence agent. Saved {len(db_insights)} insights successfully.")

if __name__ == "__main__":
    unittest.main()
