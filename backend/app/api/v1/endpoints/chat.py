"""
Chat API Endpoints — CEO Conversational Assistant.

POST /api/v1/chat/         — Submit a message and get a strategic response.
GET  /api/v1/chat/history  — Retrieve the active memory context for the company.
"""

import sys
import os
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.api.deps import get_current_active_user
from app.core.rate_limiter import RateLimiter

logger = logging.getLogger("market-strategist-chat")

router = APIRouter()


# -------------------------------------------------------------------------
# Pydantic schemas
# -------------------------------------------------------------------------
class ChatTurn(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatTurn]] = []


class CitationItem(BaseModel):
    score: float = 0.0
    source_type: str = "unknown"
    title: str = "Untitled"
    competitor_name: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    insight_type: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    citations: List[Dict[str, Any]] = []
    suggestion_cards: List[str] = []


# -------------------------------------------------------------------------
# POST /chat/
# -------------------------------------------------------------------------
@router.post("/", response_model=ChatResponse, dependencies=[Depends(RateLimiter(limit=10, window=60, limit_by_ip=False))])
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a message to the CEO AI Strategic Assistant.

    The assistant:
    1. Searches the Qdrant vector store for relevant competitor intelligence
       (strictly filtered by the current user's company ID).
    2. Loads persisted memory context (preferences, goals).
    3. Generates a structured strategic response with citations and suggestions.
    4. Asynchronously updates the memory store with any new context from the message.
    """
    # Resolve the active company for this user
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=404,
            detail="No company profile found. Please complete onboarding first.",
        )

    company_id = company.id
    user_message = payload.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Build conversation history list for the agent
    history = [{"role": turn.role, "content": turn.content} for turn in (payload.conversation_history or [])]

    # Import agent inline to avoid circular imports at module load
    try:
        # Add backend path for agent imports
        backend_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "agents")
        )
        agents_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
        )
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)

        from agents.ceo_assistant import run_ceo_assistant
        from agents.memory_agent import update_memory

        # Run the CEO Assistant RAG pipeline
        result = run_ceo_assistant(
            company_id=company_id,
            user_message=user_message,
            conversation_history=history,
        )

        # Fire-and-forget memory update (catches exceptions silently)
        try:
            update_memory(company_id=company_id, user_message=user_message)
        except Exception as mem_error:
            logger.warning(f"Memory update failed (non-critical): {mem_error}")

        return ChatResponse(
            message=result.get("message", ""),
            citations=result.get("citations", []),
            suggestion_cards=result.get("suggestion_cards", []),
        )

    except Exception as e:
        logger.error(f"CEO Assistant pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assistant pipeline error: {str(e)}")


# -------------------------------------------------------------------------
# GET /chat/history
# -------------------------------------------------------------------------
@router.get("/history", dependencies=[Depends(RateLimiter(limit=100, window=60, limit_by_ip=True))])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve the current memory context for the user's active company.
    Returns the stored user preferences, company goals, and conversation context.
    """
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        return {"memories": {}}

    try:
        agents_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
        )
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)

        from agents.memory_agent import get_memories
        memories = get_memories(company_id=company.id)
        return {"memories": memories, "company_id": company.id}

    except Exception as e:
        logger.error(f"Failed to retrieve chat history/memories: {e}")
        return {"memories": {}}
