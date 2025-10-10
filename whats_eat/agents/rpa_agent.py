"""Restaurant Profile Agent - collects and structures place data"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from ..tools.places import place_text_search, place_details_batch
from ..tools.kg import kg_upsert
from ..tools.vector import vector_embed_and_upsert
from ..schemas import RestaurantDoc

PROMPT = """You are the Restaurant Profile Agent (RPA).
Your task is to collect and structure restaurant data from Places API.

Workflow:
1. Use place_text_search to collect candidates
2. Use place_details_batch for rich data
3. Structure as RestaurantDoc objects
4. Upsert to KG and vector store (best-effort)

Rules:
1. Return 20-50 candidates per search
2. Project to minimal RestaurantDoc fields
3. Clean and normalize cuisine tags
4. Generate short_desc for vector search
5. Handle API errors gracefully"""

def build_rpa_agent():
    """Build the Restaurant Profile Agent with places and storage tools"""
    return create_react_agent(
        model=ChatOpenAI(model="gpt-4o"),
        tools=[
            place_text_search,
            place_details_batch, 
            kg_upsert,
            vector_embed_and_upsert
        ],
        prompt=PROMPT,
        name="restaurant_profile_agent"
    )