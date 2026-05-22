import os
import sys
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Add agents directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.main import app
from app.models.base import Base
from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.company import Company
from app.models.competitor import Competitor
from app.models.insights import Insight
from app.models.recommendations import Recommendation
from app.models.events import CompetitorEvent
from app.models.alerts import Alert

class TestDashboardTriggerPipeline(unittest.TestCase):
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
        
        # Create all tables in the SQLite database
        print("METADATA TABLES:", Base.metadata.tables.keys())
        Base.metadata.create_all(bind=self.engine)
        
        # Create a test session
        self.db = self.TestingSessionLocal()
        
        # Seed test user
        self.user = User(
            id=1,
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
            id=1,
            name="My Enterprise SaaS",
            website="https://myenterprise.com",
            industry="Software Automation",
            services="Workflow builder and predictive automation pipelines.",
            user_id=self.user.id
        )
        self.db.add(self.company)
        self.db.commit()
        self.db.refresh(self.company)
        
        # Seed test competitor
        self.competitor = Competitor(
            id=1,
            company_id=self.company.id,
            name="Competitor X",
            website="https://competitorx.com",
            linkedin_url="https://linkedin.com/company/competitorx"
        )
        self.db.add(self.competitor)
        self.db.commit()
        self.db.refresh(self.competitor)
        
        # Setup overrides for FastAPI dependencies
        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        def override_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        # Setup overrides in all agent modules to use our in-memory SQLite SessionLocal
        import agents.website_monitor
        import agents.social_intelligence
        import agents.news_agent
        import agents.market_research
        import agents.recommendation
        
        self.original_sessions = {
            "website_monitor": agents.website_monitor.SessionLocal,
            "social_intelligence": agents.social_intelligence.SessionLocal,
            "news_agent": agents.news_agent.SessionLocal,
            "market_research": agents.market_research.SessionLocal,
            "recommendation": agents.recommendation.SessionLocal,
        }
        
        agents.website_monitor.SessionLocal = self.TestingSessionLocal
        agents.social_intelligence.SessionLocal = self.TestingSessionLocal
        agents.news_agent.SessionLocal = self.TestingSessionLocal
        agents.market_research.SessionLocal = self.TestingSessionLocal
        agents.recommendation.SessionLocal = self.TestingSessionLocal
        
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()
        
        import agents.website_monitor
        import agents.social_intelligence
        import agents.news_agent
        import agents.market_research
        import agents.recommendation
        
        agents.website_monitor.SessionLocal = self.original_sessions["website_monitor"]
        agents.social_intelligence.SessionLocal = self.original_sessions["social_intelligence"]
        agents.news_agent.SessionLocal = self.original_sessions["news_agent"]
        agents.market_research.SessionLocal = self.original_sessions["market_research"]
        agents.recommendation.SessionLocal = self.original_sessions["recommendation"]

    def test_pipeline_trigger(self):
        # Call the POST /api/v1/dashboard/trigger endpoint
        response = self.client.post("/api/v1/dashboard/trigger")
        if response.status_code != 200:
            print("ERROR RESPONSE:", response.text)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("executed strategic analysis pipeline", data["message"].lower())
        
        # Verify insights were created in SQLite
        insights = self.db.query(Insight).all()
        # Should have:
        # - 1 general baseline event (from website_monitor baseline crawl)
        # - social summary insights (from social_intelligence)
        # - news insights (from news_agent)
        # - market discovery insights (from market_research)
        self.assertTrue(len(insights) > 0)
        
        # Check that we have a market insight
        market_insights = [i for i in insights if i.insight_type == "market"]
        self.assertTrue(len(market_insights) > 0)
        
        # Check that recommendations were created in SQLite
        recommendations = self.db.query(Recommendation).all()
        self.assertTrue(len(recommendations) > 0)
        
        # Verify GET /api/v1/insights retrieves them
        insights_res = self.client.get("/api/v1/insights/")
        self.assertEqual(insights_res.status_code, 200)
        self.assertTrue(len(insights_res.json()) > 0)
        
        # Verify GET /api/v1/recommendations retrieves them
        recs_res = self.client.get("/api/v1/recommendations/")
        self.assertEqual(recs_res.status_code, 200)
        self.assertTrue(len(recs_res.json()) > 0)
        
        # Test PUT /api/v1/recommendations/{id}
        rec_id = recommendations[0].id
        put_res = self.client.put(f"/api/v1/recommendations/{rec_id}", json={"status": "implemented"})
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json()["status"], "implemented")
        
        print(f"Integration pipeline successfully verified. Seeded {len(insights)} insights and {len(recommendations)} recommendations. PUT update verified.")

if __name__ == "__main__":
    unittest.main()
