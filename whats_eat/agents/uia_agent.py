"""User Intent Agent - extracts structured query from natural language"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..schemas import QuerySpec, Geo

PROMPT = """You are the User Intent Agent (UIA).
Your task is to extract a structured QuerySpec from the user's natural language request.

Rules:
1. Only output valid QuerySpec JSON (follow the schema exactly)
2. Infer reasonable radius if location mentioned (default 2000m)
3. Parse price bands ("cheap" = $, "moderate" = $$, "expensive" = $$$)
4. Handle diet restrictions and party size if mentioned
5. Use consistent cuisine categories (american, chinese, italian, etc.)

Example input: "Looking for cheap sushi near downtown, for 4 people"
Example output: {
  "geo": {"lat": <downtown_lat>, "lng": <downtown_lng>, "radius": 2000},
  "price_band": "$",
  "cuisines": ["japanese", "sushi"],
  "party_size": 4
}

You cannot see the location. Return a QuerySpec with location as None if no specific place mentioned."""

def build_uia_agent():
    """Build the User Intent Agent with its prompt and tools"""
    return create_react_agent(
        model=ChatOpenAI(model="gpt-4o"),
        tools=[],  # No tools needed - pure NLP extraction
        prompt=PROMPT,
        name="user_intent_agent",
    )