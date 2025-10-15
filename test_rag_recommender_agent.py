"""
Test the RAG Recommender Agent
Tests the complete pipeline: ingestion → search → ranking → output
"""

import json
import asyncio
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment first
from whats_eat.app.env_loader import load_env
load_env()

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from whats_eat.tools.RAG import process_places_data, query_similar_places_tool
from whats_eat.tools.ranking import rank_restaurants_by_profile, filter_by_attributes


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


def build_test_agent():
    """Build the RAG recommender agent for testing"""
    return create_react_agent(
        model=init_chat_model("openai:gpt-4o-mini"),
        tools=[
            process_places_data,
            query_similar_places_tool,
            rank_restaurants_by_profile,
            filter_by_attributes
        ],
        name="rag_recommender_agent",
    )


async def _test_rag_recommender_agent_async():
    """Test the RAG recommender agent with sample data"""
    
    print("=" * 80)
    print("🧪 TESTING RAG RECOMMENDER AGENT")
    print("=" * 80)
    
    # Step 1: Load test data
    print("\n[Step 1] Loading test data...")
    place_data, user_profile = load_test_data()
    print(f"✓ Loaded {len(place_data)} restaurants")
    print(f"✓ User preferences: {', '.join(user_profile.get('keywords', []))}")
    
    # Step 2: Build the agent
    print("\n[Step 2] Building RAG recommender agent...")
    agent = build_test_agent()
    print("✓ Agent initialized successfully")
    
    # Step 3: Prepare test message
    print("\n[Step 3] Preparing test message with place data and user profile...")
    
    # Create a realistic message as if from supervisor
    message_content = f"""
I have gathered restaurant data and user preferences. Please process this information and provide personalized recommendations.

PLACE DATA (from places_agent):
{json.dumps(place_data, indent=2)}

USER PROFILE (from user_profile_agent):
{json.dumps({
    "keywords": user_profile.get("keywords", []),
    "attributes": user_profile.get("attributes", {})
}, indent=2)}

Please:
1. Process and store the place data in Neo4j and Pinecone
2. Perform semantic similarity search based on user preferences
3. Rank the results using multi-factor scoring
4. Return the top 5 recommendations with detailed explanations
"""
    
    test_message = HumanMessage(content=message_content)
    print("✓ Test message prepared")
    
    # Step 4: Invoke the agent
    print("\n[Step 4] Invoking RAG recommender agent...")
    print("-" * 80)
    print("⏳ Processing... (this may take 30-60 seconds)")
    print("   - Connecting to Neo4j and Pinecone")
    print("   - Generating embeddings via OpenAI")
    print("   - Performing vector similarity search")
    print("   - Calculating ranking scores")
    print("-" * 80)
    
    try:
        result = await agent.ainvoke(
            {"messages": [test_message]},
            config={"configurable": {"thread_id": "test_rag_recommender"}}
        )
        
        print("\n✅ Agent execution completed successfully!")
        print("=" * 80)
        
        # Step 5: Display results
        print("\n[Step 5] Agent Response:")
        print("=" * 80)
        
        # Extract the final message
        messages = result.get("messages", [])
        if messages:
            final_message = messages[-1]
            print(f"\n{final_message.content}\n")
        else:
            print("⚠️ No messages in response")
        
        print("=" * 80)
        
        # Step 6: Verify components
        print("\n[Step 6] Verification Summary:")
        print("-" * 80)
        
        # Check if response contains expected elements
        response_text = str(final_message.content) if messages else ""
        
        checks = {
            "Contains recommendations": "recommendation" in response_text.lower(),
            "Has restaurant names": any(place['displayName']['text'] in response_text for place in place_data),
            "Includes scoring": "score" in response_text.lower() or "match" in response_text.lower(),
            "Has addresses": "address" in response_text.lower() or "Ave" in response_text or "Blvd" in response_text,
            "Mentions preferences": any(kw.lower() in response_text.lower() for kw in user_profile.get('keywords', [])[:3]),
        }
        
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {'PASS' if passed else 'FAIL'}")
        
        print("-" * 80)
        
        all_passed = all(checks.values())
        if all_passed:
            print("\n🎉 ALL CHECKS PASSED! Agent is working correctly.")
        else:
            print("\n⚠️ Some checks failed. Review the output above.")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during agent execution:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\nPossible causes:")
        print("  - Neo4j connection failed (check NEO4J_URI, NEO4J_PASSWORD)")
        print("  - Pinecone connection failed (check PINECONE_API_KEY)")
        print("  - OpenAI API failed (check OPENAI_API_KEY)")
        print("  - Network connectivity issues")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        return None


def test_rag_recommender_agent():
    """Test wrapper that runs the async test"""
    asyncio.run(_test_rag_recommender_agent_async())


async def _test_minimal_workflow_async():
    """Test minimal workflow without user profile"""
    
    print("\n\n" + "=" * 80)
    print("🧪 TESTING MINIMAL WORKFLOW (No User Profile)")
    print("=" * 80)
    
    print("\n[Test 2] Building agent...")
    agent = build_test_agent()
    
    # Load only place data
    base_path = Path(__file__).parent
    with open(base_path / 'tests' / 'place_test.json', 'r', encoding='utf-8') as f:
        place_data = json.load(f)
    
    message_content = f"""
I have restaurant data but no user profile. Please provide general recommendations.

PLACE DATA:
{json.dumps(place_data, indent=2)}

USER PROFILE:
{{}}

Please process this data and return top 3 recommendations based on ratings and general popularity.
"""
    
    print("\n[Test 2] Invoking agent with no user profile...")
    
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=message_content)]},
            config={"configurable": {"thread_id": "test_minimal"}}
        )
        
        print("✅ Minimal workflow completed!")
        
        messages = result.get("messages", [])
        if messages:
            print("\nResponse:")
            print("-" * 80)
            print(messages[-1].content)
            print("-" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return None


def test_minimal_workflow():
    """Test wrapper that runs the async test"""
    asyncio.run(_test_minimal_workflow_async())


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("RAG RECOMMENDER AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("\nThis test will:")
    print("  1. Test full workflow with place data + user profile")
    print("  2. Test minimal workflow with place data only")
    print("  3. Verify all components are working correctly")
    print("\n⚠️  REQUIREMENTS:")
    print("  - Neo4j database must be accessible")
    print("  - Pinecone API must be accessible")
    print("  - OpenAI API must be accessible")
    print("  - All credentials in .env file must be valid")
    print("\n" + "=" * 80)
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    print("\n\n🚀 Starting tests...\n")
    
    # Test 1: Full workflow
    result1 = asyncio.run(_test_rag_recommender_agent_async())
    
    # Test 2: Minimal workflow
    result2 = asyncio.run(_test_minimal_workflow_async())
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    test_results = {
        "Full workflow (with user profile)": result1 is not None,
        "Minimal workflow (without user profile)": result2 is not None,
    }
    
    for test_name, passed in test_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 80)
    
    if all(test_results.values()):
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe RAG Recommender Agent is working correctly!")
        print("You can now use it in production via the supervisor.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review the errors above and check:")
        print("  - Database connections (Neo4j, Pinecone)")
        print("  - API keys (.env file)")
        print("  - Network connectivity")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
