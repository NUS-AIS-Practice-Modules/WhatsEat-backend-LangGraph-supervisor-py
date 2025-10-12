"""Test script for RAG agent with TEST.JSON data"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables before importing tools
from whats_eat.app.env_loader import load_env
load_env()

from whats_eat.tools.RAG import process_places_data, query_similar_places_tool, RAGTools


def test_basic_normalization():
    """Test basic JSON loading and normalization without external services"""
    print("=" * 80)
    print("Testing RAG Agent - Basic Data Normalization")
    print("=" * 80)
    
    # Path to test JSON file
    test_json_path = Path(__file__).parent / "TEST.JSON"
    
    print(f"\n📁 Loading data from: {test_json_path}")
    print(f"   File exists: {test_json_path.exists()}")
    
    try:
        # Directly test the RAGTools methods without needing OpenAI
        rag_tools = RAGTools.__new__(RAGTools)  # Create instance without __init__
        
        # Load JSON data
        data = rag_tools.load_json_data(str(test_json_path))
        print(f"\n✅ Loaded {len(data)} places from JSON")
        
        # Normalize each place
        normalized = []
        for raw in data:
            doc = rag_tools._normalize_place(raw)
            if doc:
                normalized.append(doc)
        
        print(f"\n📊 Normalized {len(normalized)} places:")
        print("-" * 80)
        
        for i, place in enumerate(normalized, 1):
            print(f"\n{i}. {place.get('name', 'N/A')}")
            print(f"   Place ID: {place.get('place_id', 'N/A')}")
            print(f"   Address: {place.get('formatted_address', 'N/A')}")
            print(f"   Rating: {place.get('rating', 'N/A')}")
            print(f"   Types: {place.get('types', [])}")
        
        return normalized
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_process_places_data():
    """Test processing places data from TEST.JSON with full pipeline"""
    print("\n" + "=" * 80)
    print("Testing RAG Agent - Full Processing Pipeline")
    print("=" * 80)
    
    # Check for required environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    print("\n🔑 Environment Check:")
    print(f"   OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Missing'}")
    print(f"   NEO4J_PASSWORD: {'✓ Set' if neo4j_password else '✗ Missing'}")
    print(f"   PINECONE_API_KEY: {'✓ Set' if pinecone_key else '✗ Missing'}")
    
    if not openai_key:
        print("\n⚠️  Skipping full pipeline test - OpenAI API key not configured")
        print("   Set OPENAI_API_KEY in whats_eat/.env.json to enable this test")
        return None
    
    # Path to test JSON file
    test_json_path = Path(__file__).parent / "TEST.JSON"
    
    print(f"\n📁 Loading data from: {test_json_path}")
    
    try:
        # Test with ACTUAL Neo4j and Pinecone connections
        print("\n🔄 Processing with REAL Neo4j and Pinecone connections...")
        print("   This will create knowledge graph nodes and vector embeddings")
        result = process_places_data.invoke({
            "json_file_path": str(test_json_path),
            "dry_run": False  # ACTUAL connections to Neo4j and Pinecone
        })
        
        print("\n✅ Processing completed successfully!")
        print("\n📊 Normalized Results:")
        print("-" * 80)
        
        # Parse and display results
        data = json.loads(result)
        print(f"Total places processed: {len(data)}")
        
        for i, place in enumerate(data, 1):
            print(f"\n{i}. {place.get('name', 'N/A')}")
            print(f"   Place ID: {place.get('place_id', 'N/A')}")
            print(f"   Address: {place.get('formatted_address', 'N/A')}")
            print(f"   Rating: {place.get('rating', 'N/A')}")
        
        return data
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_query_similar_places():
    """Test querying similar places (requires Pinecone connection)"""
    print("\n" + "=" * 80)
    print("Testing RAG Agent - Query Similar Places from Pinecone")
    print("=" * 80)
    
    try:
        query = "Thai BBQ restaurant"
        print(f"\n🔍 Searching Pinecone for: '{query}'")
        print("   Performing vector similarity search...")
        
        result = query_similar_places_tool.invoke({
            "query_text": query,
            "top_k": 3
        })
        
        print("\n✅ Query completed successfully!")
        print("\n📊 Search Results:")
        print("-" * 80)
        
        data = json.loads(result)
        matches = data.get("matches", [])
        
        if not matches:
            print("   No matches found (possibly no data in index yet)")
        else:
            for i, match in enumerate(matches, 1):
                print(f"\n{i}. Score: {match.get('score', 'N/A'):.4f}")
                metadata = match.get('metadata', {})
                print(f"   Name: {metadata.get('name', 'N/A')}")
                print(f"   Address: {metadata.get('address', 'N/A')}")
                print(f"   Rating: {metadata.get('rating', 'N/A')}")
        
        return data
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   This is expected if Pinecone is not configured or no data is indexed.")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🚀 Starting RAG Agent Tests\n")
    
    # Test 1: Basic normalization (no API keys needed)
    normalized_data = test_basic_normalization()
    
    # Test 2: Full processing pipeline with REAL connections
    processed_data = test_process_places_data()
    
    # Test 3: Query similar places with REAL Pinecone search
    if processed_data:
        print("\n⏳ Waiting 2 seconds for indexing to complete...")
        import time
        time.sleep(2)
        test_query_similar_places()
    
    print("\n" + "=" * 80)
    print("✨ Test completed!")
    print("=" * 80)
