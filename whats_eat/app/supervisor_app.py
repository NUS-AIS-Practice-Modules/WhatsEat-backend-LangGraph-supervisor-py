# app/supervisor_app.py
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage

from whats_eat.langgraph_supervisor import (
    create_supervisor,
    create_forward_message_tool,
)  # your package

from whats_eat.agents.places_agent import build_places_agent
from whats_eat.agents.user_profile_agent import build_user_profile_agent
from whats_eat.agents.summarizer_agent import build_summarizer_agent
from whats_eat.agents.route_agent import build_route_agent
from whats_eat.agents.rag_recommender_agent import build_rag_recommender_agent


def build_app():
    places = build_places_agent()
    user_profile = build_user_profile_agent()
    summarizer = build_summarizer_agent()
    route = build_route_agent()
    rag_recommender = build_rag_recommender_agent()

    # Optional extra tool: forward a worker's exact wording to the user
    forward_tool = create_forward_message_tool()


    supervisor_prompt = (
        "You are the Supervisor in the What's Eat system.\n"
        "On each turn, decide whether to delegate the task to exactly ONE agent or to finish the process once all required information is complete.\n"
        "\n"
        "Core mechanism:\n"
        "After receiving a user input, you must call places_agent and user_profile_agent in parallel by issuing a single parallel tool call that includes both transfers.\n"
        "Once both return their JSON outputs, combine them in the format (json1, json2) and pass the result to rag_recommender_agent,\n"
        "which performs knowledge-enhanced retrieval and ranking.\n"
        "Finally, send the rag_recommender_agent result to summarizer_agent to generate the final human-readable answer.\n"
        "\n"
        "---\n"
        "\n"
        "Available Agents:\n"
        "- places_agent – Retrieves and analyzes information about places, restaurants, or local venues; handles geocoding (converts addresses to latitude/longitude). Must return at least 10 candidate restaurants for later ranking.\n"
        "- user_profile_agent – Generates a structured user profile from long-term YouTube behavior and current intent. Produces one unified embedding vector and structured attributes describing preferences such as cuisine type, budget, or dining style.\n"
        "- rag_recommender_agent – Unified module for Knowledge Graph Retrieval + Ranking.\n"
        "  - Input: (json1, json2), where\n"
        "      json1 = output of places_agent\n"
        "      json2 = output of user_profile_agent\n"
        "  - Performs the following steps:\n"
        "      1. Applies hard filters based on user attributes (e.g., cuisine, budget, open_now, distance).\n"
        "      2. Performs retrieval-style enrichment using external knowledge (e.g., restaurant specialties, reviews, popularity).\n"
        "      3. Uses the single embedding vector from the user profile to compute similarity and ranking scores.\n"
        "      4. Outputs the top N ranked restaurants with fields like rank, reason, score, applied_filters, and distance_km.\n"
        "- summarizer_agent – Combines and refines the output from rag_recommender_agent to produce the final natural-language summary for the user.\n"
        "\n"
        "---\n"
        "\n"
        "Standard Workflow (Restaurant Recommendation Pipeline):\n"
        "1. Parallel Phase\n"
        "   - places_agent: retrieves and geocodes at least 10 candidate restaurants near the user's specified or inferred location.\n"
        "   - user_profile_agent: generates structured user attributes and a single embedding vector.\n"
        "2. Merge & Transfer\n"
        "   - After both agents finish, combine their JSON outputs as (json1, json2) (json1 = places_agent, json2 = user_profile_agent).\n"
        "   - Send the merged result to rag_recommender_agent for knowledge-enhanced filtering and ranking.\n"
        "3. Ranking Phase (Inside rag_recommender_agent)\n"
        "   - Enrich candidates with external restaurant knowledge.\n"
        "   - Compute similarity and ranking based on the single user embedding vector.\n"
        "4. Generate Final Output\n"
        "   - Pass rag_recommender_agent results to summarizer_agent to create a polished, natural-language recommendation summary.\n"
        "5. Finish\n"
        "   - Once summarizer_agent output is received, return it directly to the user and stop the workflow.\n"
        "\n"
        "---\n"
        "\n"
        "Routing & Rules:\n"
        "- Location / Address → Coordinates (User or Restaurant) → places_agent\n"
        "- YouTube behavior / interest profiling → user_profile_agent\n"
        "- Recommendation, retrieval enhancement, or ranking → rag_recommender_agent (requires (json1, json2) input)\n"
        "- When all information is ready, produce the final answer → summarizer_agent (called exactly once)\n"
        "\n"
        "---\n"
        "\n"
        "Data Contract (Key Fields):\n"
        "- places_agent output: ≥10 candidates with fields name, lat, lng, price_level, cuisine, open_now, rating, features, source_refs.\n"
        "- user_profile_agent output: attributes, embedding_vector, keywords, notes.\n"
        "- Merged format: (json1, json2) → json1 = places, json2 = profile.\n"
        "- rag_recommender_agent output: items[] (with rank, reason, score, applied_filters, distance_km) + optional debug_signals.\n"
        "\n"
        "---\n"
        "\n"
        "Interaction Guidelines:\n"
        "- The Supervisor does not perform retrieval, filtering, or ranking itself; it only coordinates and routes tasks.\n"
        "- If user input lacks critical information (e.g., location, cuisine, or budget), ask one brief clarification question before proceeding.\n"
        "- Once summarizer_agent has produced the final JSON output, the process is complete; never call it again unless new information is introduced."
    )
    workflow = create_supervisor(
        agents=[places, user_profile, rag_recommender, summarizer, route],
        model=init_chat_model("openai:gpt-4o-mini"),
        tools=[forward_tool],              # your handoff tools will be auto-added
        prompt=supervisor_prompt,
        add_handoff_messages=False,         # omit "transfer" messages
        add_handoff_back_messages=False,    # omit "transfer back" messages
        output_mode="last_message",        # or "full_history" to include full traces
        include_agent_name="inline",       # robust name exposure for models
        parallel_tool_calls=True,         # 1-at-a-time handoffs (tutorial style)
        finalizer=_keep_user_and_summarizer_messages,
    )
    return workflow.compile()


def _keep_user_and_summarizer_messages(state: dict) -> dict:
    """Prune intermediate agent outputs before returning the final graph state."""

    messages = state.get("messages")
    if not messages:
        return state

    visible_messages: list[BaseMessage] = []
    for message in messages:
        if message.type == "human" or getattr(message, "name", None) == "summarizer_agent":
            visible_messages.append(message)

    return {
        **state,
        "messages": visible_messages,
    }
