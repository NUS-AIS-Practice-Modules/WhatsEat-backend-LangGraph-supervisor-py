# app/supervisor_app.py
from langchain.chat_models import init_chat_model
from whats_eat.langgraph_supervisor import create_supervisor, create_forward_message_tool  # your package

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
        "You are the supervisor. On each turn decide whether to delegate to exactly ONE agent or to finish the task.\n"
        "- Available agents:\n"
        "  • places_agent – retrieves and analyzes information about places, restaurants, or local venues; GEOCODES any addresses (user or restaurant) to lat/long.\n"
        "  • user_profile_agent – converts YouTube behaviour into structured dining preferences and embeddings.\n"
        "  • rag_recommender_agent – COMBINED agent that handles the complete recommendation pipeline:\n"
        "    * Accepts TWO JSON inputs from supervisor: place data (from places_agent) AND user profile data\n"
        "    * Builds knowledge graph (Neo4j) + vector embeddings (Pinecone) from place data\n"
        "    * Performs semantic similarity search using user profile embeddings\n"
        "    * Ranks results with multi-factor scoring (similarity 35%, rating 25%, attributes 25%, distance 15%)\n"
        "    * Returns ranked recommendations as formatted text\n"
        "    * Replaces the old separate rag_agent and recommender_agent workflow\n"
        "  • summarizer_agent – combines and refines results from other agents to generate the final, human-readable response.\n"
        "  • route_agent – computes routes and generates interactive map views GIVEN coordinates (lat/long); does not perform geocoding.\n"
        "  • rag_agent – performs retrieval-augmented generation for answering questions using knowledge base or document search.\n"
        "- Routing guide:\n"
        "  • Location/place search or address→coordinates (user or restaurant) → places_agent\n"
        "  • YouTube history, channels, or interest-based profiling → user_profile_agent\n"
        "  • Get personalized restaurant recommendations → places_agent → (optional: user_profile_agent) → rag_recommender_agent → summarizer_agent\n"
        "  • Routing / map visualization when coordinates are known → route_agent\n"
        "  • When all required information has been gathered, produce the final answer → summarizer_agent exactly once.\n"
        "- Do not solve tasks yourself. Use handoff tools to delegate when additional work is required.\n"
        "- If the request is unclear or missing critical information (e.g., starting address or selected restaurant), ask ONE short clarifying question before delegating.\n"
        "- Multi-step handling (typical flows):\n"
        "  • Place search only: places_agent → summarizer_agent\n"
        "  • Personalized recommendations: places_agent → user_profile_agent → rag_recommender_agent → summarizer_agent\n"
        "  • Quick recommendations (no user profile): places_agent → rag_recommender_agent → summarizer_agent\n"
        "  • Route/map: places_agent (geocode addresses to lat/long) → route_agent (compute route & map) → summarizer_agent\n"
        "- CRITICAL: When routing to rag_recommender_agent, ensure:\n"
        "  1. Place data is available in conversation (from places_agent)\n"
        "  2. User profile is available if personalization requested (from user_profile_agent)\n"
        "  3. Forward BOTH datasets in your handoff message to rag_recommender_agent\n"
        "- Pass only coordinates (lat/long) to route_agent; do not pass raw addresses.\n"
        "- After summarizer_agent produces the final JSON, stop delegating and end the run. Never re-call summarizer_agent without new information.\n"
        "- The summarizer_agent output is the final response shown to the user.\n"
        "- IMPORTANT: Once summarizer_agent provides the final answer, the conversation is COMPLETE. Do not route to any other agents.\n"
        "- If you receive a response from summarizer_agent, forward it directly to the user and STOP."

    )

    workflow = create_supervisor(
        agents=[places, user_profile, rag_recommender, summarizer, route],
        model=init_chat_model("openai:gpt-4o-mini"),
        tools=[forward_tool],              # your handoff tools will be auto-added
        prompt=supervisor_prompt,
        # add_handoff_back_messages=True,    # include "transfer back" messages
        add_handoff_messages=False,  # keep graph memory compact for API responses
        add_handoff_back_messages=False,  # return only the final AI message to clients
        output_mode="last_message",        # or "full_history" to include full traces
        include_agent_name="inline",       # robust name exposure for models
        parallel_tool_calls=False,         # 1-at-a-time handoffs (tutorial style)
    )
    return workflow.compile()
