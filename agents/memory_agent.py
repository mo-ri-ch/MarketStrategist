"""
Memory Agent — Agent 7

LangGraph workflow that extracts user preferences, strategic goals, and
contextual notes from conversation turns, then persists them to the `memories`
PostgreSQL table for later retrieval by the CEO Assistant (Agent 8).

Workflow:
  load_existing → extract_merge → save_memory → END
"""

import os
import sys
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional

# Allow imports from app.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from langgraph.graph import StateGraph, END
from app.db.session import SessionLocal
from app.models.memory import Memory
from app.models.company import Company

logger = logging.getLogger("memory-agent")

# -------------------------------------------------------------------------
# State definition
# -------------------------------------------------------------------------
class MemoryAgentState(TypedDict):
    company_id: int
    user_message: str           # Latest user chat message to parse
    existing_memories: Dict[str, Any]
    updated_memories: Dict[str, Any]


# -------------------------------------------------------------------------
# Node: Load existing memory keys for this company
# -------------------------------------------------------------------------
def load_existing_memories(state: MemoryAgentState) -> Dict[str, Any]:
    company_id = state["company_id"]
    logger.info(f"[MemoryAgent] Loading existing memories for company {company_id}")

    db = SessionLocal()
    try:
        records = db.query(Memory).filter(Memory.company_id == company_id).all()
        memories: Dict[str, Any] = {}
        for record in records:
            memories[record.key] = record.value
        logger.info(f"[MemoryAgent] Loaded {len(memories)} memory keys: {list(memories.keys())}")
        return {"existing_memories": memories}
    finally:
        db.close()


# -------------------------------------------------------------------------
# Node: Extract meaningful context from the latest user message and merge
# -------------------------------------------------------------------------
def extract_and_merge(state: MemoryAgentState) -> Dict[str, Any]:
    message = state.get("user_message", "").strip()
    existing = state.get("existing_memories", {})

    if not message:
        logger.info("[MemoryAgent] No user message provided, skipping extraction.")
        return {"updated_memories": existing}

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        # Fallback: keyword-based extraction
        logger.info("[MemoryAgent] No OpenAI key — using keyword-based memory extraction.")
        updated = dict(existing)

        lowered = message.lower()

        # Extract conversation context snippet
        ctx = updated.get("conversation_context", [])
        if not isinstance(ctx, list):
            ctx = []
        ctx.append(message[-500:])  # Keep last 500 chars of each message
        if len(ctx) > 20:
            ctx = ctx[-20:]  # Rolling window of last 20 turns
        updated["conversation_context"] = ctx

        # Extract goal signals
        goal_keywords = ["goal", "aim", "objective", "target", "want to", "trying to", "focus on"]
        if any(kw in lowered for kw in goal_keywords):
            updated["company_goals"] = (updated.get("company_goals") or "") + f"\n[USER NOTE] {message}"

        # Extract preference signals
        pref_keywords = ["prefer", "like", "always", "never", "don't", "do not", "make sure", "remind"]
        if any(kw in lowered for kw in pref_keywords):
            updated["user_preferences"] = (updated.get("user_preferences") or "") + f"\n[PREFERENCE] {message}"

        return {"updated_memories": updated}

    # LLM-based extraction
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        existing_str = json.dumps(existing, indent=2, default=str)
        prompt = f"""
You are a strategic memory extraction assistant for a CEO intelligence platform.
Analyze this new user message and the existing memory store, then return an UPDATED memory store JSON.

Current memory store:
{existing_str}

New user message:
\"{message}\"

Instructions:
1. Append the message to "conversation_context" (a list), keep last 20 entries only.
2. If the message expresses a business goal or objective, append it to "company_goals" (string).
3. If the message expresses a user preference or instruction, append it to "user_preferences" (string).
4. Do not delete existing data. Merge and extend.
5. Return ONLY valid JSON with the full updated memory store.
"""

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You output only valid JSON with no markdown wrappers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        updated = json.loads(content)
        logger.info("[MemoryAgent] LLM extraction successful.")
        return {"updated_memories": updated}

    except Exception as e:
        logger.error(f"[MemoryAgent] LLM extraction failed: {e}. Preserving existing memories.")
        return {"updated_memories": existing}


# -------------------------------------------------------------------------
# Node: Persist updated memory keys to PostgreSQL
# -------------------------------------------------------------------------
def save_memories(state: MemoryAgentState) -> Dict[str, Any]:
    company_id = state["company_id"]
    updated = state.get("updated_memories", {})

    if not updated:
        logger.info("[MemoryAgent] No memories to save.")
        return {}

    db = SessionLocal()
    try:
        for key, value in updated.items():
            existing_record = db.query(Memory).filter(
                Memory.company_id == company_id,
                Memory.key == key
            ).first()

            if existing_record:
                existing_record.value = value
            else:
                db.add(Memory(company_id=company_id, key=key, value=value))

        db.commit()
        logger.info(f"[MemoryAgent] Saved {len(updated)} memory keys for company {company_id}.")
    except Exception as e:
        db.rollback()
        logger.error(f"[MemoryAgent] Failed to save memories: {e}")
    finally:
        db.close()

    return {}


# -------------------------------------------------------------------------
# Build and compile the LangGraph workflow
# -------------------------------------------------------------------------
workflow = StateGraph(MemoryAgentState)

workflow.add_node("load_existing", load_existing_memories)
workflow.add_node("extract_merge", extract_and_merge)
workflow.add_node("save_memory", save_memories)

workflow.set_entry_point("load_existing")
workflow.add_edge("load_existing", "extract_merge")
workflow.add_edge("extract_merge", "save_memory")
workflow.add_edge("save_memory", END)

run_memory_agent = workflow.compile()


# -------------------------------------------------------------------------
# Convenience helper
# -------------------------------------------------------------------------
def update_memory(company_id: int, user_message: str) -> Dict[str, Any]:
    """
    Run the memory agent to extract and save context from a user message.

    Args:
        company_id: The ID of the active company.
        user_message: The latest message text from the user.

    Returns:
        The updated memories dictionary.
    """
    initial_state: MemoryAgentState = {
        "company_id": company_id,
        "user_message": user_message,
        "existing_memories": {},
        "updated_memories": {},
    }
    final_state = run_memory_agent.invoke(initial_state)
    return final_state.get("updated_memories", {})


def get_memories(company_id: int) -> Dict[str, Any]:
    """
    Load all stored memory keys for a company directly from the database.

    Args:
        company_id: The ID of the active company.

    Returns:
        A dict of memory key → value pairs.
    """
    db = SessionLocal()
    try:
        records = db.query(Memory).filter(Memory.company_id == company_id).all()
        return {r.key: r.value for r in records}
    finally:
        db.close()
