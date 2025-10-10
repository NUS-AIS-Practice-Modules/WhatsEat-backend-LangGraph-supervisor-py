"""Preference Fusion Agent - scores and ranks candidates"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..tools.scoring import rank_places
from ..tools.vector import vector_search
from ..schemas import RankedList, RankedItem

PROMPT = """You are the Preference Fusion Agent (PFA).
Your task is to rank restaurants based on query and user preferences.

Workflow:
1. Get vector search results if relevant
2. Score candidates with rank_places
3. Return RankedList with reasons

Rules:
1. Balance multiple factors in ranking
2. Provide clear 'why' reasons
3. Note any cautions/tradeoffs
4. Explain ranking rationale
5. Handle missing user profiles gracefully"""

def build_pfa_agent():
    """Build the Preference Fusion Agent with ranking tools"""
    return create_react_agent(
        model=ChatOpenAI(model="gpt-4o"),
        tools=[rank_places, vector_search],
        prompt=PROMPT,
        name="preference_fusion_agent"
    )