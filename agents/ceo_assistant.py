"""
CEO Assistant Agent — Agent 8

Conversational RAG workflow:
  1. Embeds the user query and searches Qdrant for relevant competitor context
     (filtered by company_id for strict multi-tenant isolation).
  2. Loads memory context (preferences, goals) from PostgreSQL.
  3. Assembles a rich system prompt and conversation history.
  4. Generates a strategic assistant response via LLM (or a rule-based mock).
  5. Returns structured output: message, citations, and suggestion_cards.
"""

import os
import sys
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.models.company import Company
from app.db.qdrant import get_qdrant_client, COLLECTION_NAME
from app.services.embeddings import get_embeddings
from agents.memory_agent import get_memories

logger = logging.getLogger("ceo-assistant-agent")


# -------------------------------------------------------------------------
# Helper: Search Qdrant for relevant competitor context
# -------------------------------------------------------------------------
def _search_qdrant(query: str, company_id: int, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Embed the query and perform a cosine-similarity search in Qdrant,
    restricting results strictly to the given company_id.
    """
    client = get_qdrant_client()
    query_vector = get_embeddings(query)

    try:
        # Build filter (works for both real QdrantClient and MockQdrantClient)
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            qdrant_filter = Filter(
                must=[FieldCondition(key="company_id", match=MatchValue(value=company_id))]
            )
        except ImportError:
            # MockQdrantClient uses duck-typed filter objects
            class _Match:
                def __init__(self, value):
                    self.value = value

            class _Condition:
                def __init__(self, key, match):
                    self.key = key
                    self.match = match

            class _Filter:
                def __init__(self, must):
                    self.must = must

            qdrant_filter = _Filter(
                must=[_Condition(key="company_id", match=_Match(value=company_id))]
            )

        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        citations = []
        for r in results:
            payload = r.payload if hasattr(r, "payload") else {}
            citations.append({
                "score": round(r.score, 4) if hasattr(r, "score") else 0.0,
                "source_type": payload.get("source_type", "unknown"),
                "title": payload.get("title", "Untitled"),
                "competitor_name": payload.get("competitor_name"),
                "event_type": payload.get("event_type"),
                "severity": payload.get("severity"),
                "insight_type": payload.get("insight_type"),
                "sentiment_score": payload.get("sentiment_score"),
                "created_at": payload.get("created_at"),
            })

        logger.info(f"[CeoAssistant] Qdrant returned {len(citations)} relevant documents.")
        return citations

    except Exception as e:
        logger.error(f"[CeoAssistant] Qdrant search failed: {e}")
        return []


# -------------------------------------------------------------------------
# Helper: Generate mock response (no OpenAI key)
# -------------------------------------------------------------------------
def _generate_mock_response(
    query: str,
    citations: List[Dict[str, Any]],
    memories: Dict[str, Any],
    company_name: str,
) -> Dict[str, Any]:
    """
    Rule-based response generator used when OPENAI_API_KEY is not set.
    """
    query_lower = query.lower()

    if citations:
        top = citations[0]
        comp_name = top.get("competitor_name", "a competitor")
        ev_type = top.get("event_type") or top.get("insight_type") or "activity"
        response = (
            f"Based on the latest intelligence for {company_name}, I found "
            f"{len(citations)} relevant data points. The most recent involves "
            f"**{comp_name}** with a {ev_type} event: \"{top.get('title', 'See details')}\". "
            f"This was scored at {top.get('score', 0):.0%} relevance to your query."
        )
    elif "competitor" in query_lower or "market" in query_lower:
        response = (
            f"I don't yet have indexed intelligence for this specific query about {company_name}. "
            "Try triggering the intelligence swarm first via the dashboard, then ask again."
        )
    else:
        response = (
            f"Hello! I'm your CEO Strategic Assistant for {company_name}. "
            "Ask me about competitor pricing, market trends, hiring signals, or strategic recommendations."
        )

    suggestions = [
        "What are the latest competitor pricing changes?",
        "Show me recent social media intelligence for our top competitors",
        "What strategic actions should I take this week?",
        "Are there any emerging competitors I should watch?",
    ]

    return {
        "message": response,
        "citations": citations[:5],
        "suggestion_cards": suggestions,
    }


# -------------------------------------------------------------------------
# Main: Run CEO Assistant
# -------------------------------------------------------------------------
def run_ceo_assistant(
    company_id: int,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Execute the CEO Assistant RAG pipeline for a given user query.

    Args:
        company_id: The active company's ID (used for multi-tenant filtering).
        user_message: The latest user chat message.
        conversation_history: Optional list of prior turns [{"role": ..., "content": ...}].

    Returns:
        Dict with keys: message (str), citations (list), suggestion_cards (list).
    """
    if conversation_history is None:
        conversation_history = []

    # 1. Fetch company info
    db = SessionLocal()
    company_name = "Your Company"
    company_industry = "Technology"
    company_goals = ""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company_name = company.name
            company_industry = company.industry or "Technology"
            company_goals = company.goals or ""
    finally:
        db.close()

    # 2. Search Qdrant for relevant competitor context
    citations = _search_qdrant(query=user_message, company_id=company_id, top_k=6)

    # 3. Load persistent memory context
    memories = get_memories(company_id)

    # 4. Check for LLM availability
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("[CeoAssistant] No OpenAI key — using mock response generator.")
        return _generate_mock_response(
            query=user_message,
            citations=citations,
            memories=memories,
            company_name=company_name,
        )

    # 5. Build LLM prompt with context
    context_blocks = []
    for i, c in enumerate(citations, 1):
        comp = c.get("competitor_name", "Unknown Competitor")
        title = c.get("title", "Untitled")
        source = c.get("source_type", "data")
        ev_type = c.get("event_type") or c.get("insight_type") or "activity"
        context_blocks.append(f"[{i}] {source.upper()} | {comp} | {ev_type} | \"{title}\"")

    context_str = "\n".join(context_blocks) if context_blocks else "No relevant competitor data found in the knowledge base."

    user_prefs = memories.get("user_preferences", "")
    company_goals_mem = memories.get("company_goals", company_goals)
    conv_ctx = memories.get("conversation_context", [])
    conv_summary = " | ".join(conv_ctx[-3:]) if conv_ctx else "No prior context."

    system_prompt = f"""You are the Chief AI Strategic Advisor for "{company_name}", operating in the "{company_industry}" sector.

Company Strategic Goals:
{company_goals_mem or "Not specified"}

User Preferences & Instructions:
{user_prefs or "No special preferences noted."}

Recent Conversation Context:
{conv_summary}

Relevant Intelligence Retrieved (cite by number in your response):
{context_str}

Guidelines:
- Be direct, executive-level, and actionable.
- Reference the intelligence sources by number when relevant.
- End each response with 3-4 concrete "Next Steps" the CEO should consider.
- Return your response as valid JSON with these exact keys:
  {{
    "message": "Your strategic response here (markdown supported)",
    "citations_used": [1, 3, 5],
    "suggestion_cards": ["Question 1?", "Question 2?", "Question 3?"]
  }}
"""

    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation_history[-10:]:  # Last 10 turns
        messages.append(turn)
    messages.append({"role": "user", "content": user_message})

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()

        # Strip markdown wrapper if present
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)

        # Map citation indices back to actual payloads
        used_indices = parsed.get("citations_used", [])
        used_citations = []
        for idx in used_indices:
            if 1 <= idx <= len(citations):
                used_citations.append(citations[idx - 1])

        return {
            "message": parsed.get("message", ""),
            "citations": used_citations if used_citations else citations[:3],
            "suggestion_cards": parsed.get("suggestion_cards", []),
        }

    except Exception as e:
        logger.error(f"[CeoAssistant] LLM call failed: {e}. Falling back to mock response.")
        return _generate_mock_response(
            query=user_message,
            citations=citations,
            memories=memories,
            company_name=company_name,
        )
