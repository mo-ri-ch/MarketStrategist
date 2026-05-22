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
from app.models.insights import Insight

class TestMarketResearchAgent(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        
        # Create all tables in the SQLite database
        Base.metadata.create_all(bind=self.engine)
        
        # Override SessionLocal in the agent module
        import agents.market_research as market_research
        self.original_session_local = market_research.SessionLocal
        market_research.SessionLocal = self.TestingSessionLocal
        
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
            services="Automated database creation and low-code visualization software.",
            user_id=self.user.id
        )
        self.db.add(self.company)
        self.db.commit()
        self.db.refresh(self.company)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        import agents.market_research as market_research
        market_research.SessionLocal = self.original_session_local

    def test_market_research_agent_workflow(self):
        from agents.market_research import run_market_research_agent
        
        # Invoke the LangGraph workflow
        initial_state = {
            "company_id": self.company.id,
            "company_name": "",
            "company_industry": "",
            "company_services": "",
            "discovered_competitors": [],
            "insights_to_save": []
        }
        
        result = run_market_research_agent.invoke(initial_state)
        
        # Verify competitor details were retrieved
        self.assertEqual(result["company_name"], "Target Company")
        self.assertEqual(result["company_industry"], "Software Automation")
        
        # Verify the end state has discovered competitors
        self.assertTrue(len(result["discovered_competitors"]) > 0)
        self.assertTrue(len(result["insights_to_save"]) > 0)
        
        # Verify insights were saved to the database
        db_insights = self.db.query(Insight).filter(
            Insight.company_id == self.company.id, 
            Insight.insight_type == "market"
        ).all()
        
        self.assertTrue(len(db_insights) > 0)
        print(f"Verified market research agent. Saved {len(db_insights)} discovered competitors as market insights successfully.")

if __name__ == "__main__":
    unittest.main()
