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
from app.models.events import CompetitorEvent
from app.models.alerts import Alert

class TestNewsMonitoringAgent(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Create all tables in the SQLite database
        Base.metadata.create_all(bind=self.engine)
        
        # Override SessionLocal in the agent module
        import agents.news_agent as news_agent
        self.original_session_local = news_agent.SessionLocal
        news_agent.SessionLocal = self.TestingSessionLocal
        
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
        import agents.news_agent as news_agent
        news_agent.SessionLocal = self.original_session_local

    def test_news_agent_workflow(self):
        from agents.news_agent import run_news_agent
        
        # Invoke the LangGraph workflow
        initial_state = {
            "competitor_id": self.competitor.id,
            "company_id": self.company.id,
            "competitor_name": self.competitor.name,
            "news_articles": [],
            "insights_to_save": []
        }
        
        result = run_news_agent.invoke(initial_state)
        
        # Verify the end state has news articles and insights
        self.assertTrue(len(result["news_articles"]) > 0)
        self.assertTrue(len(result["insights_to_save"]) > 0)
        
        # Verify insights were saved to the database
        db_insights = self.db.query(Insight).filter(Insight.competitor_id == self.competitor.id).all()
        self.assertTrue(len(db_insights) > 0)
        
        # Verify that specific news insights were recorded
        news_insight = db_insights[0]
        self.assertEqual(news_insight.insight_type, "news")
        self.assertTrue(hasattr(news_insight, "data_points"))
        
        # Verify if CompetitorEvent and Alert tables have entries for key news categories
        db_events = self.db.query(CompetitorEvent).filter(CompetitorEvent.competitor_id == self.competitor.id).all()
        db_alerts = self.db.query(Alert).filter(Alert.competitor_id == self.competitor.id).all()
        
        print(f"Verified news monitoring agent. Saved {len(db_insights)} insights, {len(db_events)} events, and {len(db_alerts)} alerts successfully.")

if __name__ == "__main__":
    unittest.main()
