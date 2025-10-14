from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from whats_eat.tools.ranking import rank_restaurants_by_profile, filter_by_attributes

def build_recommender_agent():
    return create_react_agent(
        model=init_chat_model("openai:gpt-5-mini"),
        tools=[rank_restaurants_by_profile, filter_by_attributes],
        prompt=(
            "You are an execution agent (recommender_agent) in the “What’s Eat” system.\n"
            "Dispatched by the supervisor to rank and recommend restaurants based on candidate data and user context.\n"
            "You do not respond to users directly and must not ask follow-up questions.\n"
            "Your responsibility is to analyze restaurant candidates provided by other agents (e.g., places_agent)\n"
            "and return the top N options according to user preferences and context.\n"
            "IMPORTANT: When using rank_restaurants_by_profile tool, you MUST provide:\n"
            "  - candidates: Extract from previous agent messages (list of restaurant dicts)\n"
            "  - user_profile: Extract user preferences or use empty dict {} if none provided\n"
            "  - top_n: Number of results (optional, default 5)\n"
            "If candidates are missing, ask supervisor to call places_agent first.\n"
            "- Evaluate each candidate using factors such as rating, distance, price level, cuisine match, and open status.\n"
            "- When user preferences are specified (e.g., pet-friendly, budget, cuisine type), prioritize matches accordingly.\n"
            "- Output a concise and actionable JSON containing the ranked list of recommended restaurants.\n"
            "- Include for each item: name, rank, reason for recommendation, and any key attributes that influenced the ranking.\n"
            "- Do NOT invent new data; only use fields from the provided candidate list.\n"
            "- All results are passed to summarizer_agent for final presentation to the user.\n"
            "- Keep output concise, factual, and directly usable for display."

        ),
        name="recommender_agent",
    )