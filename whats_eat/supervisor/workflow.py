"""WhatsEat supervisor workflow definition"""
from __future__ import annotations
from typing import Dict, Any

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph_supervisor import (
    create_supervisor,
    create_handoff_tool,
    create_forward_message_tool
)

from ..agents.uia_agent import build_uia_agent
from ..agents.upa_agent import build_upa_agent
from ..agents.rpa_agent import build_rpa_agent
from ..agents.pfa_agent import build_pfa_agent
from ..agents.eea_agent import build_eea_agent
from .prompt import SUPERVISOR_PROMPT

class WhatsEatState(BaseModel):
    query_spec: Dict[str, Any] | None = None
    user_profile: Dict[str, Any] | None = None
    candidates: list[Dict[str, Any]] | None = None
    ranking: Dict[str, Any] | None = None
    evidence: Dict[str, Any] | None = None
    audit_events: list[Dict[str, Any]] = []

def create_whatseat_supervisor():
    """Build the WhatsEat supervisor with all agents"""

    # Build all agents
    agents = {
        "uia": build_uia_agent(),
        "upa": build_upa_agent(),
        "rpa": build_rpa_agent(),
        "pfa": build_pfa_agent(), 
        "eea": build_eea_agent()
    }
    
    # Create supervisor with routing tools
    supervisor = create_supervisor(
        agents=agents,
        tools=[
            create_handoff_tool(),
            create_forward_message_tool()
        ],
        model=ChatOpenAI(model="gpt-4o"),
        prompt=SUPERVISOR_PROMPT,
        output_mode="last_message",
        initial_state=WhatsEatState()
    )

    return supervisor