"""Evidence & Enrichment Agent - adds photos, hours, links"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..tools.photos import fetch_place_photos
from ..tools.places import build_gmaps_deeplink
from ..schemas import Evidence

PROMPT = """You are the Evidence & Enrichment Agent (EEA).
Your task is to enrich top ranked places with photos and links.

Workflow:
1. Get photos for top-K places
2. Build navigation deeplinks
3. Add opening hours if available
4. Return Evidence objects

Rules:
1. Get 2-3 photos per place
2. Use appropriate photo sizes
3. Include nav links with mode
4. Add website/phone if available
5. Handle missing data gracefully"""

def build_eea_agent():
    """Build the Evidence & Enrichment Agent with media tools"""
    return create_react_agent(
        model=ChatOpenAI(model="gpt-4o"),
        tools=[fetch_place_photos, build_gmaps_deeplink],
        prompt=PROMPT,
        name="evidence_agent"
    )