"""User Profile Agent - builds taste profile from history"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..tools.youtube import yt_fetch_history, yt_topics_infer
from ..schemas import UserTasteProfile

PROMPT = """You are the User Profile Agent (UPA).
Your task is to build a UserTasteProfile by analyzing user's content history.

Workflow:
1. Get YouTube history with yt_fetch_history
2. Extract preferences with yt_topics_infer
3. Return UserTasteProfile with inferred preferences

Rules:
1. Skip YouTube if no OAuth/user_id (return empty profile)
2. Use consistent cuisine categories
3. Only include strong signals in disliked[]
4. Store raw signals in history_signals"""

def build_upa_agent():
    """Build the User Profile Agent with YouTube tools"""
    return create_react_agent(
        model=ChatOpenAI(model="gpt-4o"),
        tools=[yt_fetch_history, yt_topics_infer],
        prompt=PROMPT,
        name="user_profile_agent"
    )