<div align="center">

# 🧠 MarketStrategist
### AI-Powered Competitor Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14%2B-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B35?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

*A multi-tenant, enterprise-grade SaaS platform that autonomously monitors competitors, discovers market opportunities, tracks social and news activity, and delivers CEO-level strategic intelligence — powered by a swarm of LangGraph AI agents.*

[Features](#-features) · [Architecture](#-architecture) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [Agents](#-ai-agent-swarm) · [API](#-api-reference) · [Deployment](#-deployment) · [Contributing](#-contributing)

</div>

---

## ✨ Features

| Module | Capability |
|---|---|
| 🕷️ **Website Monitor** | Real-time Playwright scraping detecting pricing changes, product launches & hiring surges |
| 📰 **News Intelligence** | RSS + AI-classified news events — funding rounds, acquisitions, partnerships |
| 📱 **Social Intelligence** | Cross-platform tracking (X, LinkedIn, YouTube, Reddit, Instagram, Medium, Threads) |
| 🔍 **Market Discovery** | Autonomous competitor discovery via web search and business directory scanning |
| 🤖 **CEO Assistant** | RAG-powered conversational assistant with vector memory and source citations |
| 📊 **Predictive Analytics** | ML-driven competitor action forecasting with confidence scores |
| 🚨 **Smart Alerts** | LLM-graded severity alerts (High / Medium / Low) with email + webhook dispatch |
| 📄 **Weekly Reports** | Automated executive PDF digest compiled every Sunday |
| 🌐 **Multi-Region** | Geographically distributed crawler agents across US-East, EU-West, APAC |
| 🛡️ **RBAC Security** | Granular role-based access (Admin / Analyst / Viewer) on every endpoint |
| 📋 **Audit Logs** | Immutable, chronological system audit trail with admin console UI |
| ⚡ **Rate Limiting** | Redis sliding-window rate limiter (5 req/min sensitive, 30 req/min general) |
| 🗄️ **Smart Caching** | TTL-based Redis response cache with mutation-triggered invalidation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 14)                       │
│  Dashboard · Competitors · Market · Assistant · Alerts · Audit Logs │
└────────────────────────────┬────────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────────┐
│                        BACKEND (FastAPI)                             │
│  Auth · Company · Competitors · Dashboard · Chat · Predictor         │
│  Reports · Insights · Recommendations · Audit · Alerts               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │  Qdrant (Vector DB)      │  │
│  │  (Primary DB)│  │Cache + Queue │  │  Embeddings + RAG Memory │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Celery Tasks
┌────────────────────────────▼────────────────────────────────────────┐
│                      AI AGENT SWARM (LangGraph)                      │
│                                                                     │
│  Agent 1: Website Monitor      Agent 2: Social Intelligence         │
│  Agent 3: News Agent           Agent 4: Market Research             │
│  Agent 5: Recommendation       Agent 6: Alert Agent                 │
│  Agent 7: Memory Agent         Agent 8: CEO Assistant (RAG)         │
│  Agent 9: Regional Crawler                                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Task Queue | Celery + Redis |
| Vector Store | Qdrant |
| AI Agents | LangGraph + LangChain |
| Embeddings / LLM | OpenAI (`text-embedding-3-small`, `gpt-4o`) |
| Web Scraping | Playwright |
| PDF Generation | ReportLab |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Caching | Redis (TTL-based JSON cache) |
| Rate Limiting | Redis sliding-window counters |

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS + custom glassmorphism |
| Fonts | Inter + Outfit (Google Fonts) |
| HTTP Client | Native fetch + React hooks |

### Infrastructure
| Layer | Technology |
|---|---|
| Container Orchestration | Docker Compose (dev + prod) |
| Kubernetes | 9 production manifests (deployments, services, PVCs, ingress) |
| Ingress Controller | Nginx |
| CI/CD Ready | GitHub Actions compatible |

---

## 📁 Repository Structure

```
MarketStrategist/
├── 🖥️  frontend/                   # Next.js 14 application
│   └── src/
│       ├── app/
│       │   ├── dashboard/          # All dashboard pages
│       │   │   ├── page.tsx        # Main intelligence console
│       │   │   ├── competitors/    # Competitor management + predictions
│       │   │   ├── market/         # Market trends + positioning matrix
│       │   │   ├── alerts/         # Strategic notifications
│       │   │   ├── assistant/      # CEO conversational chat
│       │   │   ├── recommendations/# CEO strategy advice board
│       │   │   └── audit/          # Admin audit log console
│       │   ├── login/              # Auth pages
│       │   ├── signup/
│       │   └── onboarding/         # Multi-step onboarding wizard
│       └── components/             # Reusable UI components
│
├── ⚙️  backend/                    # FastAPI service
│   ├── app/
│   │   ├── api/v1/endpoints/       # All REST API controllers
│   │   │   ├── auth.py             # JWT auth + user management
│   │   │   ├── company.py          # Company profile + settings
│   │   │   ├── competitors.py      # Competitor CRUD
│   │   │   ├── dashboard.py        # Metrics, events, crawl triggers
│   │   │   ├── chat.py             # CEO assistant chat API
│   │   │   ├── predictor.py        # Action forecasting
│   │   │   ├── reports.py          # PDF report generation
│   │   │   ├── alerts.py           # Alert management
│   │   │   ├── insights.py         # Social + news insights
│   │   │   ├── recommendations.py  # Strategic recommendations
│   │   │   └── audit.py            # Immutable audit logs (admin)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # Business logic services
│   │   │   ├── rate_limiter.py     # Redis rate limiting
│   │   │   ├── cache_manager.py    # Redis caching
│   │   │   ├── audit_logger.py     # Immutable audit log writer
│   │   │   ├── predictor.py        # Predictive analytics
│   │   │   ├── anomaly_detector.py # Statistical anomaly detection
│   │   │   ├── notifications.py    # Email + webhook dispatcher
│   │   │   ├── embeddings.py       # Vector embedding service
│   │   │   ├── regional_filter.py  # Multi-region filtering
│   │   │   ├── news_fetcher.py     # RSS + news aggregation
│   │   │   └── social_scraper.py   # Social media analytics
│   │   ├── workers/                # Celery async workers
│   │   │   └── tasks/
│   │   │       ├── scraper.py      # Playwright website scraper
│   │   │       ├── indexer.py      # Qdrant vector indexer
│   │   │       └── report_generator.py # Weekly PDF compiler
│   │   ├── core/                   # Core utilities
│   │   │   ├── security.py         # JWT + password hashing
│   │   │   └── rbac.py             # Role-based access control
│   │   └── db/
│   │       ├── session.py          # SQLAlchemy session
│   │       └── qdrant.py           # Qdrant client + collections
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # Pytest test suites
│   └── requirements.txt
│
├── 🤖 agents/                      # LangGraph AI agent workflows
│   ├── website_monitor.py          # Agent 1: Website change detection
│   ├── social_intelligence.py      # Agent 2: Social media monitoring
│   ├── news_agent.py               # Agent 3: News event classification
│   ├── market_research.py          # Agent 4: Competitor discovery
│   ├── recommendation.py           # Agent 5: CEO strategic advice
│   ├── alert_agent.py              # Agent 6: Severity evaluation
│   ├── memory_agent.py             # Agent 7: Conversation memory
│   ├── ceo_assistant.py            # Agent 8: RAG conversational AI
│   └── regional_crawler.py         # Agent 9: Multi-region scraping
│
├── 🐳 docker/                      # Docker configurations
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── prod.docker-compose.yml     # Production stack
│
├── ☸️  kubernetes/                 # Kubernetes production manifests
│   ├── k8s-configmap.yaml
│   ├── k8s-secrets.yaml
│   ├── postgres-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── qdrant-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── celery-worker-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── ingress.yaml
│
├── docker-compose.yml              # Local development stack
└── tasks.md                        # Full implementation tasklist
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** ≥ 24.0
- **Node.js** ≥ 18.0 (for frontend dev)
- **Python** ≥ 3.11 (for backend dev)
- An **OpenAI API key** (for LLM + embeddings features)

### 1. Clone the Repository

```bash
git clone https://github.com/mo-ri-ch/MarketStrategist.git
cd MarketStrategist
```

### 2. Configure Environment Variables

```bash
# Copy and edit the backend environment file
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/competitor_intelligence

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant Vector DB
QDRANT_URL=http://localhost:6333

# AI / LLM
OPENAI_API_KEY=sk-...

# Auth
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Start with Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, Qdrant, Backend, Frontend, Celery)
docker-compose up --build

# Services will be available at:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

### 4. Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the Platform

Open [http://localhost:3000](http://localhost:3000), create an account, and follow the onboarding wizard to set up your company profile and add competitors.

---

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload --port 8000

# Run Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:3000
```

---

## 🤖 AI Agent Swarm

MarketStrategist operates a coordinated swarm of **9 specialized LangGraph agents**, each responsible for a distinct monitoring and reasoning task:

| # | Agent | Role | Triggers |
|---|---|---|---|
| 1 | **Website Monitor** | Scrapes competitor websites via Playwright, diffs content between runs, classifies changes (pricing, products, hiring) | Celery scheduled task |
| 2 | **Social Intelligence** | Tracks follower growth, sentiment, and engagement across 7 platforms | Celery scheduled task |
| 3 | **News Agent** | Aggregates RSS feeds, classifies funding/acquisition/partnership news with LLM | Celery scheduled task |
| 4 | **Market Research** | Autonomously discovers unmanaged competitors via search and business directories | On-demand / Celery |
| 5 | **Recommendation** | Synthesizes all signals into CEO-level strategic advice cards with confidence scores | Post-monitoring run |
| 6 | **Alert Agent** | Evaluates competitor event severity (High/Medium/Low) using LLM + rule heuristics | On every new event |
| 7 | **Memory Agent** | Persists user preferences, conversation themes, and company goals to semantic memory | Post-chat session |
| 8 | **CEO Assistant** | RAG-powered chat: retrieves Qdrant vectors + memories, generates cited strategic answers | User chat message |
| 9 | **Regional Crawler** | Simulates geographically distributed scraping across US-East, EU-West, APAC | Celery scheduled task |

---

## 🔐 Security & Access Control

### Role Hierarchy

| Role | Permissions |
|---|---|
| `admin` | Full access — audit logs, user role management, all write operations, pipeline triggers |
| `analyst` | Competitor CRUD, predictions, reports, recommendations — no audit logs or user management |
| `viewer` | Read-only access to all dashboard data, no write operations |

### Rate Limiting

| Route Type | Limit |
|---|---|
| Auth endpoints (`/login`, `/signup`) | 5 requests / minute |
| General API endpoints | 30 requests / minute |

Rate limiting uses **Redis sliding-window counters** and fails open gracefully when Redis is unavailable.

### Audit Logging

Every sensitive action is recorded in an **immutable audit log**: login events, competitor additions/deletions, settings changes, pipeline triggers, and report generation. Audit logs are write-only — no update or delete routes exist.

---

## 📡 API Reference

Interactive API documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

### Core Endpoints

```
POST   /api/v1/auth/signup                    Register a new user
POST   /api/v1/auth/login                     Authenticate and receive JWT
PATCH  /api/v1/auth/users/{id}/role           Update user role (admin only)

GET    /api/v1/company/my-company             Get company profile
PATCH  /api/v1/company/my-company             Update company settings

GET    /api/v1/competitors                    List all tracked competitors
POST   /api/v1/competitors                    Add a new competitor
DELETE /api/v1/competitors/{id}               Remove a competitor

GET    /api/v1/dashboard/metrics              Aggregated intelligence metrics
GET    /api/v1/dashboard/events               Chronological competitor events
POST   /api/v1/dashboard/trigger              Trigger full monitoring swarm
GET    /api/v1/dashboard/regional-status      Multi-region crawler health

GET    /api/v1/chat/history                   Retrieve conversation history
POST   /api/v1/chat/message                   Send message to CEO Assistant

GET    /api/v1/predictor/{competitor_id}      Get action forecast
POST   /api/v1/predictor/{competitor_id}/refresh  Recalculate prediction

POST   /api/v1/reports/weekly/trigger         Generate and email weekly PDF

GET    /api/v1/alerts                         List strategic alerts
PATCH  /api/v1/alerts/{id}                    Mark alert read/unread
DELETE /api/v1/alerts/{id}                    Dismiss alert

GET    /api/v1/audit                          System audit log (admin only)
```

---

## ☸️ Deployment

### Production Docker Compose

```bash
# Uses docker/prod.docker-compose.yml
docker-compose -f docker/prod.docker-compose.yml up -d
```

### Kubernetes

All manifests are in the `/kubernetes` directory. Deploy in order:

```bash
# 1. Create namespace and base configs
kubectl apply -f kubernetes/k8s-configmap.yaml
kubectl apply -f kubernetes/k8s-secrets.yaml      # ⚠️ Fill in real values first!

# 2. Data layer
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/redis-deployment.yaml
kubectl apply -f kubernetes/qdrant-deployment.yaml

# 3. Application layer
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/celery-worker-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml

# 4. Traffic routing
kubectl apply -f kubernetes/ingress.yaml
```

> **⚠️ Important:** Before deploying, replace the placeholder values in `kubernetes/k8s-secrets.yaml` with real base64-encoded production credentials. Never commit real secrets to source control.

### Environment Variables Reference

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `REDIS_URL` | Redis connection string | ✅ |
| `QDRANT_URL` | Qdrant vector DB URL | ✅ |
| `OPENAI_API_KEY` | OpenAI API key for LLM + embeddings | ✅ |
| `SECRET_KEY` | JWT signing secret (≥32 chars) | ✅ |
| `SMTP_HOST` | SMTP server for email alerts | Optional |
| `SMTP_USER` | SMTP login email | Optional |
| `SMTP_PASSWORD` | SMTP app password | Optional |

---

## 🧪 Testing

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific phase tests
python -m pytest tests/test_phase5.py -v     # Security, caching & rate limiting
python -m pytest tests/test_phase4.py -v     # Alert agent, anomaly detection, predictor
```

Current test coverage:
- ✅ Rate limiter under-limit, over-limit, and Redis fail-safe
- ✅ Cache get/set and mutation-triggered invalidation
- ✅ Alert agent severity evaluation
- ✅ Notification dispatcher (email + webhook)
- ✅ Anomaly detector baseline comparison
- ✅ Competitor action predictor heuristics

---

## 📈 Development Roadmap

- [x] **Phase 0** — Core infrastructure, Docker, database schema
- [x] **Phase 1** — Auth, company onboarding, competitor management, website monitoring
- [x] **Phase 2** — Social media, news, market discovery, recommendation engine
- [x] **Phase 3** — Vector RAG, memory agent, CEO conversational assistant
- [x] **Phase 4** — Alerts, notifications, anomaly detection, predictive analytics, PDF reports
- [x] **Phase 5** — Multi-region scaling, RBAC, audit logs, caching, Kubernetes deployment
- [ ] **Phase 6** *(Planned)* — White-label multi-tenancy, billing integration, mobile app

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">

Built with ❤️ using FastAPI, LangGraph, Next.js, and a swarm of AI agents.

</div>
