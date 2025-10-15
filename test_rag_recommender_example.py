"""
Test script for the RAG Recommender Agent
Demonstrates how to use the combined agent with sample data
"""

import json
from pathlib import Path

# Sample usage example for the RAG Recommender Agent

def load_test_data():
    """Load test data files"""
    base_path = Path(__file__).parent
    
    # Load place data
    with open(base_path / 'tests' / 'place_test.json', 'r', encoding='utf-8') as f:
        place_data = json.load(f)
    
    # Load user profile
    with open(base_path / 'tests' / 'user_profile_example.json', 'r', encoding='utf-8') as f:
        user_profile = json.load(f)
    
    return place_data, user_profile


def format_supervisor_message(place_data, user_profile):
    """
    Format the message that supervisor would send to rag_recommender_agent
    """
    message = f"""
I have gathered the following information for the recommendation request:

PLACE DATA (from places_agent):
{json.dumps(place_data, indent=2)}

USER PROFILE (from user_profile_agent):
{json.dumps(user_profile, indent=2)}

Please process this data and provide personalized restaurant recommendations.
Use the complete pipeline:
1. Store place data in Neo4j and Pinecone
2. Perform semantic similarity search based on user preferences
3. Rank results using multi-factor scoring
4. Return top 5 recommendations with detailed explanations
"""
    return message


def main():
    """
    Example workflow showing how supervisor forwards data to rag_recommender_agent
    """
    print("=" * 80)
    print("RAG RECOMMENDER AGENT - TEST EXAMPLE")
    print("=" * 80)
    
    # Step 1: Load test data
    print("\n[Step 1] Loading test data...")
    place_data, user_profile = load_test_data()
    
    print(f"✓ Loaded {len(place_data)} restaurants")
    print(f"✓ User preferences: {', '.join(user_profile.get('keywords', []))}")
    
    # Step 2: Format supervisor message
    print("\n[Step 2] Formatting supervisor message...")
    supervisor_msg = format_supervisor_message(place_data, user_profile)
    
    # Step 3: Show expected agent behavior
    print("\n[Step 3] Expected Agent Processing Flow:")
    print("-" * 80)
    print("The rag_recommender_agent will:")
    print("  1️⃣  Extract place data JSON from the message")
    print("  2️⃣  Call process_places_data() to build knowledge graph")
    print("     → Neo4j: Store Place nodes and Review relationships")
    print("     → Pinecone: Index 1536-dim embeddings for each place")
    print()
    print("  3️⃣  Build search query from user profile:")
    user_keywords = ' '.join(user_profile.get('keywords', []))
    print(f"     Query: '{user_keywords}'")
    print()
    print("  4️⃣  Call query_similar_places_tool() for semantic search")
    print("     → Pinecone: Vector similarity search (top 20 candidates)")
    print()
    print("  5️⃣  Call rank_restaurants_by_profile() for multi-factor ranking")
    print("     → Similarity: 35% weight")
    print("     → Rating: 25% weight")
    print("     → Attributes: 25% weight (cuisine, price, diet, style)")
    print("     → Distance: 15% weight")
    print()
    print("  6️⃣  Return formatted text with top 5 recommendations")
    print("-" * 80)
    
    # Step 4: Show expected output format
    print("\n[Step 4] Expected Output Format:")
    print("-" * 80)
    expected_output = """
🎯 TOP RECOMMENDATIONS FOR USER

Based on preferences: food challenges, street food, Malaysian, Japanese, Chinese
Total candidates analyzed: 20
Top 5 recommendations:

1. Eem - Thai BBQ & Cocktails
   📍 Address: 3808 N Williams Ave #127, Portland, OR 97227, USA
   ⭐ Rating: 4.5 (234 reviews)
   💰 Price: MODERATE
   🎨 Type: Thai, Bar
   📊 Match Score: 0.8542 / 1.0
   💡 Why: Strong Asian cuisine match, excellent ratings with many reviews,
           moderate price fits mid-range budget, street food style compatible

2. Por Qué No?
   📍 Address: 3524 N Mississippi Ave, Portland, OR 97227, USA
   ⭐ Rating: 4.3 (189 reviews)
   💰 Price: INEXPENSIVE
   🎨 Type: Mexican, Street Food
   📊 Match Score: 0.7821 / 1.0
   💡 Why: Perfect street food style match, budget-friendly pricing,
           high user ratings, good proximity score

[... 3 more recommendations ...]
"""
    print(expected_output)
    print("-" * 80)
    
    # Step 5: Integration notes
    print("\n[Step 5] Integration with Supervisor:")
    print("-" * 80)
    print("Typical request flow:")
    print()
    print("  User: 'Find me Malaysian street food restaurants in Portland'")
    print()
    print("  Supervisor workflow:")
    print("    1. places_agent ← Search Portland restaurants")
    print("    2. user_profile_agent ← Extract preferences from context/YouTube")
    print("    3. rag_recommender_agent ← Process + Rank + Recommend")
    print("    4. summarizer_agent ← Polish final response")
    print("    5. Return to user")
    print("-" * 80)
    
    print("\n✅ Test example complete!")
    print("\nTo run the actual agent, start the LangGraph server:")
    print("  python -m uv run langgraph dev")
    print("\nThen send requests to: http://127.0.0.1:2024")
    print()


if __name__ == "__main__":
    main()
