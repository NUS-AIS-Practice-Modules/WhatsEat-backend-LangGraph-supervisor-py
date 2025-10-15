# app/supervisor_app.py
from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph._internal._runnable import RunnableCallable
from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel
from langgraph.prebuilt.chat_agent_executor import AgentState

from whats_eat.langgraph_supervisor import create_forward_message_tool, create_supervisor
from whats_eat.langgraph_supervisor.supervisor import OutputMode, _make_call_agent

from whats_eat.agents.places_agent import build_places_agent
from whats_eat.agents.user_profile_agent import build_user_profile_agent
from whats_eat.agents.recommender_agent import build_recommender_agent
from whats_eat.agents.summarizer_agent import build_summarizer_agent
from whats_eat.agents.route_agent import build_route_agent
from whats_eat.agents.RAG_agent import build_rag_agent


PARALLEL_AGENT_NAME = "places_user_profile_parallel_agent"


def _merge_parallel_results(
    results: Sequence[Any],
    *,
    agent_name: str,
) -> AgentState:
    """Merge outputs from parallel agent executions into a single state update."""

    combined_messages: list[AnyMessage] = []
    state_updates: dict[str, Any] = {}
    status_messages: list[str] = []

    for subagent_name, result in zip(
        ("places_agent", "user_profile_agent"),
        results,
    ):
        if isinstance(result, Exception):
            status_messages.append(f"{subagent_name} failed: {result}")
            continue

        combined_messages.extend(result.get("messages", []))
        for key, value in result.items():
            if key == "messages":
                continue
            state_updates[key] = value
        status_messages.append(f"{subagent_name} completed successfully.")

    if not status_messages:
        status_messages.append("No responses were returned from parallel agents.")

    combined_messages.append(
        AIMessage(
            content="Parallel dispatch finished. " + " ".join(status_messages),
            name=agent_name,
        )
    )

    state_updates["messages"] = combined_messages
    return state_updates


def build_parallel_places_user_profile_agent(
    places_agent: Pregel,
    user_profile_agent: Pregel,
    *,
    output_mode: OutputMode,
    add_handoff_back_messages: bool = False,
) -> Pregel:
    """Create a subgraph that executes places and user profile agents in parallel."""

    places_runner = _make_call_agent(
        places_agent,
        output_mode,
        add_handoff_back_messages=add_handoff_back_messages,
        supervisor_name=PARALLEL_AGENT_NAME,
    )
    user_profile_runner = _make_call_agent(
        user_profile_agent,
        output_mode,
        add_handoff_back_messages=add_handoff_back_messages,
        supervisor_name=PARALLEL_AGENT_NAME,
    )

    def _invoke_parallel_sync(state: AgentState, config: RunnableConfig) -> AgentState:
        results: list[Any] = []
        for runner in (places_runner, user_profile_runner):
            try:
                results.append(runner.invoke(state, config))
            except Exception as exc:  # noqa: BLE001 - propagate error details to supervisor
                results.append(exc)
        return _merge_parallel_results(results, agent_name=PARALLEL_AGENT_NAME)

    async def _invoke_parallel_async(
        state: AgentState,
        config: RunnableConfig,
    ) -> AgentState:
        results = await asyncio.gather(
            places_runner.ainvoke(state, config),
            user_profile_runner.ainvoke(state, config),
            return_exceptions=True,
        )
        return _merge_parallel_results(results, agent_name=PARALLEL_AGENT_NAME)

    parallel_graph = StateGraph(AgentState)
    parallel_graph.add_node(
        PARALLEL_AGENT_NAME,
        RunnableCallable(_invoke_parallel_sync, _invoke_parallel_async),
    )
    parallel_graph.add_edge(START, PARALLEL_AGENT_NAME)
    parallel_graph.add_edge(PARALLEL_AGENT_NAME, END)
    return parallel_graph.compile(name=PARALLEL_AGENT_NAME)

def build_app():
    output_mode: OutputMode = "last_message"

    places = build_places_agent()
    user_profile = build_user_profile_agent()
    parallel_places_user_profile = build_parallel_places_user_profile_agent(
        places,
        user_profile,
        output_mode=output_mode,
    )
    recommender = build_recommender_agent()
    summarizer = build_summarizer_agent()
    route = build_route_agent()
    rag = build_rag_agent()

    # Optional extra tool: forward a worker's exact wording to the user
    forward_tool = create_forward_message_tool()

    supervisor_prompt = (
        "You are the supervisor. On each turn decide whether to delegate to exactly ONE agent or to finish the task.\n"
        "- Available agents:\n"
        "  • places_user_profile_parallel_agent – dispatches places_agent and user_profile_agent simultaneously and merges their outputs into a combined update.\n"
        "  • places_agent – retrieves and analyzes information about places, restaurants, or local venues; GEOCODES any addresses (user or restaurant) to lat/long.\n"
        "  • user_profile_agent – converts YouTube behaviour into structured dining preferences and embeddings.\n"
        "  • recommender_agent – ranks, filters, or selects items (e.g., recommends top places based on taste, location, or user preferences).\n"
        "  • summarizer_agent – combines and refines results from other agents to generate the final, human-readable response.\n"
        "  • route_agent – computes routes and generates interactive map views GIVEN coordinates (lat/long); does not perform geocoding.\n"
        "  • rag_agent – performs retrieval-augmented generation for answering questions using knowledge base or document search.\n"
        "- Routing guide:\n"
        "  • Location/place search or address→coordinates (user or restaurant) → places_agent\n"
        "  • Need BOTH personalization insights and place discovery → places_user_profile_parallel_agent (runs places_agent + user_profile_agent in parallel)\n"
        "  • YouTube history, channels, or interest-based profiling → user_profile_agent\n"
        "  • Knowledge-based questions or document retrieval → rag_agent\n"
        "  • Ranking, comparison, or shortlisting → recommender_agent\n"
        "  • Routing / map visualization when coordinates are known → route_agent\n"
        "  • When all required information has been gathered, produce the final answer → summarizer_agent exactly once.\n"
        "- Do not solve tasks yourself. Use handoff tools to delegate when additional work is required.\n"
        "- If the request is unclear or missing critical information (e.g., starting address or selected restaurant), ask ONE short clarifying question before delegating.\n"
        "- Multi-step handling (typical flows):\n"
        "  • Place search only: places_agent → summarizer_agent\n"
        "  • Recommendations: places_user_profile_parallel_agent → recommender_agent → summarizer_agent\n"
        "  • Route/map: places_agent (geocode addresses to lat/long) → route_agent (compute route & map) → summarizer_agent\n"
        "- Pass only coordinates (lat/long) to route_agent; do not pass raw addresses.\n"
        "- After summarizer_agent produces the final JSON, stop delegating and end the run. Never re-call summarizer_agent without new information.\n"
        "- The summarizer_agent output is the final response shown to the user.\n"
        "- IMPORTANT: Once summarizer_agent provides the final answer, the conversation is COMPLETE. Do not route to any other agents.\n"
        "- If you receive a response from summarizer_agent, forward it directly to the user and STOP."

    )

    workflow = create_supervisor(
        agents=[
            parallel_places_user_profile,
            places,
            user_profile,
            recommender,
            summarizer,
            route,
            rag,
        ],
        model=init_chat_model("openai:gpt-4o-mini"),
        tools=[forward_tool],              # your handoff tools will be auto-added
        prompt=supervisor_prompt,
        # add_handoff_back_messages=True,    # include "transfer back" messages
        add_handoff_messages=False,  # keep graph memory compact for API responses
        add_handoff_back_messages=False,  # return only the final AI message to clients
        output_mode=output_mode,            # or "full_history" to include full traces
        include_agent_name="inline",       # robust name exposure for models
        parallel_tool_calls=False,         # 1-at-a-time handoffs (tutorial style)
    )
    return workflow.compile()
