from whats_eat.agents.RAG_agent import RAGAgent
import json

def print_divider(title):
    print("\n" + "="*50)
    print(title)
    print("="*50)

# Initialize agent
agent = RAGAgent()

# Process test.json
print_divider("Processing test.json")
processed = agent.process_places_data("tests/test.json")
print(f"Processed {len(processed)} places")

# Query Neo4j
print_divider("Checking Neo4j data")
with agent.neo4j_driver.session() as session:
    # Count places
    result = session.run("MATCH (p:Place) RETURN count(p) as count")
    count = result.single()["count"]
    print(f"Places in Neo4j: {count}")
    
    # Get all places
    result = session.run("MATCH (p:Place) RETURN p.name, p.place_id, p.address")
    places = [dict(record['p']) for record in result]
    print("\nStored places:")
    print(json.dumps(places, indent=2))

# Query Pinecone
print_divider("Testing vector search")
results = agent.query_similar_places("thai food near portland")
print("\nSearch results:")
print(json.dumps(results.to_dict(), indent=2))