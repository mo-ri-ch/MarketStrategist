"""
Knowledge Base Document Indexer — Celery Tasks.

Indexes competitor events, social insights, and news data from PostgreSQL
into the Qdrant vector store for semantic retrieval by the CEO Assistant.
All indexed documents carry a `company_id` payload for multi-tenant filtering.
"""

import os
import sys
import json
import logging
import uuid
from typing import Optional

# Allow imports from app.* in the backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.qdrant import get_qdrant_client, COLLECTION_NAME
from app.services.embeddings import get_embeddings
from app.models.events import CompetitorEvent
from app.models.insights import Insight
from app.models.competitor import Competitor

logger = logging.getLogger("market-strategist-indexer")


def _upsert_to_qdrant(doc_id: str, text: str, payload: dict):
    """
    Helper: embed text and upsert a single point into Qdrant.
    """
    client = get_qdrant_client()
    vector = get_embeddings(text)

    try:
        # Use real qdrant_client models if available
        from qdrant_client.models import PointStruct
        point = PointStruct(id=doc_id, vector=vector, payload=payload)
    except ImportError:
        # Fallback: plain object for MockQdrantClient
        class _Point:
            def __init__(self, id, vector, payload):
                self.id = id
                self.vector = vector
                self.payload = payload
        point = _Point(id=doc_id, vector=vector, payload=payload)

    client.upsert(collection_name=COLLECTION_NAME, points=[point])
    logger.info(f"Indexed document '{doc_id}' into Qdrant collection '{COLLECTION_NAME}'.")


@celery_app.task(name="app.workers.tasks.indexer.index_competitor_event")
def index_competitor_event(event_id: int):
    """
    Celery task: fetch a CompetitorEvent from PostgreSQL, embed its semantic
    content, and upsert it into the Qdrant vector store.
    """
    db = SessionLocal()
    try:
        event = db.query(CompetitorEvent).filter(CompetitorEvent.id == event_id).first()
        if not event:
            logger.warning(f"CompetitorEvent id={event_id} not found. Skipping index.")
            return

        competitor = db.query(Competitor).filter(Competitor.id == event.competitor_id).first()
        company_id = competitor.company_id if competitor else None

        # Build semantic text chunk
        text = (
            f"Competitor: {competitor.name if competitor else 'Unknown'}. "
            f"Event Type: {event.event_type}. "
            f"Title: {event.title}. "
            f"Details: {event.description}. "
            f"Severity: {event.severity}."
        )

        payload = {
            "source_type": "competitor_event",
            "event_id": event.id,
            "competitor_id": event.competitor_id,
            "competitor_name": competitor.name if competitor else "Unknown",
            "company_id": company_id,
            "event_type": event.event_type,
            "title": event.title,
            "severity": event.severity,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

        # Use a deterministic UUID from event_id so re-indexing is idempotent
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"event:{event_id}"))
        _upsert_to_qdrant(doc_id=doc_id, text=text, payload=payload)

    except Exception as e:
        logger.error(f"Failed to index CompetitorEvent id={event_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.indexer.index_social_insight")
def index_social_insight(insight_id: int):
    """
    Celery task: fetch a social Insight from PostgreSQL, embed its content,
    and upsert it into the Qdrant vector store.
    """
    db = SessionLocal()
    try:
        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            logger.warning(f"Insight id={insight_id} not found. Skipping index.")
            return

        # Build semantic text chunk
        data_points_str = json.dumps(insight.data_points or {})
        text = (
            f"Social Intelligence Insight — Type: {insight.insight_type}. "
            f"Title: {insight.title}. "
            f"Description: {insight.description}. "
            f"Sentiment Score: {insight.sentiment_score:.2f}. "
            f"Data Points: {data_points_str}."
        )

        payload = {
            "source_type": "social_insight",
            "insight_id": insight.id,
            "competitor_id": insight.competitor_id,
            "company_id": insight.company_id,
            "insight_type": insight.insight_type,
            "title": insight.title,
            "sentiment_score": insight.sentiment_score,
            "created_at": insight.created_at.isoformat() if insight.created_at else None,
        }

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"insight:{insight_id}"))
        _upsert_to_qdrant(doc_id=doc_id, text=text, payload=payload)

    except Exception as e:
        logger.error(f"Failed to index Insight id={insight_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.indexer.index_all_company_data")
def index_all_company_data(company_id: int):
    """
    Celery task: bulk re-index all CompetitorEvents and Insights for a company.
    Safe to call multiple times — Qdrant upserts are idempotent via UUID v5.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting bulk re-index for company_id={company_id}")

        # Get all competitor IDs for this company
        competitors = db.query(Competitor).filter(Competitor.company_id == company_id).all()
        comp_ids = [c.id for c in competitors]

        if not comp_ids:
            logger.info(f"No competitors found for company {company_id}. Nothing to index.")
            return

        # Index all CompetitorEvents
        events = db.query(CompetitorEvent).filter(
            CompetitorEvent.competitor_id.in_(comp_ids)
        ).all()

        logger.info(f"Indexing {len(events)} competitor events for company {company_id}...")
        for event in events:
            index_competitor_event.delay(event.id)

        # Index all social Insights
        insights = db.query(Insight).filter(Insight.company_id == company_id).all()

        logger.info(f"Indexing {len(insights)} social insights for company {company_id}...")
        for insight in insights:
            index_social_insight.delay(insight.id)

        logger.info(
            f"Bulk re-index dispatched: {len(events)} events + {len(insights)} insights "
            f"for company {company_id}."
        )

    except Exception as e:
        logger.error(f"Failed bulk re-index for company {company_id}: {e}")
        raise
    finally:
        db.close()
