# RAG Recommender Agent Guide

## Overview

The **RAG Recommender Agent** is a combined agent that integrates RAG (Retrieval-Augmented Generation) capabilities with intelligent ranking to provide personalized restaurant recommendations.

### What It Replaces

This single agent replaces the previous two-agent workflow:
- ❌ OLD: `rag_agent` (embedding + search) → `recommender_agent` (ranking)
- ✅ NEW: `rag_recommender_agent` (complete pipeline)

## Input Requirements

The agent expects **TWO JSON datasets** forwarded by the supervisor:

### 1. Place Data (from `places_agent`)

Example structure (similar to `tests/place_test.json`):

```json
[
  {
    "id": "ChIJOa08KlqnlVQR_ZZx1jEcTYY",
    "displayName": {
      "text": "Eem - Thai BBQ & Cocktails",
      "languageCode": "en"
    },
    "formattedAddress": "3808 N Williams Ave #127, Portland, OR 97227, USA",
    "location": {
      "latitude": 45.5506551,
      "longitude": -122.66652119999998
    },
    "rating": 4.5,
    "userRatingCount": 234,
    "priceLevel": "PRICE_LEVEL_MODERATE",
    "types": ["thai_restaurant", "bar"]
  }
]
```

**Required fields:**
- `id` or `place_id`: Unique identifier
- `displayName.text` or `name`: Restaurant name
- `formattedAddress`: Full address
- `location`: {latitude, longitude}

**Optional but recommended:**
- `rating`: 0.0-5.0
- `userRatingCount`: Number of reviews
- `priceLevel`: PRICE_LEVEL_INEXPENSIVE | MODERATE | EXPENSIVE | VERY_EXPENSIVE
- `types`: Array of category tags

### 2. User Profile Data (from `user_profile_agent`)

Example structure (similar to `tests/user_profile_example.json`):

```json
{
  "keywords": [
    "food challenges",
    "street food",
    "Malaysian",
    "Japanese"
  ],
  "attributes": {
    "style": ["street food", "casual"],
    "region": ["Malaysian", "Japanese", "Chinese"],
    "price_band": "mid",
    "diet": ["vegetarian"]
  },
  "embedding": [/* 1536-dimensional vector */]
}
```

**Key fields:**
- `keywords`: Array of preference keywords
- `attributes.style`: Dining style preferences
- `attributes.region`: Cuisine/region preferences
- `attributes.price_band`: "budget" | "mid" | "upscale"
- `attributes.diet`: Dietary restrictions
- `embedding`: 1536-dim OpenAI embedding vector (optional, for semantic search)

## Processing Pipeline

The agent executes a 4-step pipeline:

### Step 1: Build Knowledge Base (RAG Ingestion)

```
Place Data → Neo4j Graph + Pinecone Vectors
```

**Tool:** `process_places_data(places_data=<json_string>, dry_run=False)`

**Actions:**
1. Stores structured data in Neo4j knowledge graph
2. Generates embeddings using OpenAI `text-embedding-3-small` (1536 dims)
3. Indexes vectors in Pinecone for similarity search

### Step 2: Semantic Search

```
User Profile → Query Vector → Similarity Search → Candidates
```

**Tool:** `query_similar_places_tool(query=<search_text>, top_k=20)`

**Actions:**
1. Converts user keywords/attributes to search query
2. Performs vector similarity search in Pinecone
3. Returns top-k candidates with similarity scores

### Step 3: Intelligent Ranking

```
Candidates + User Profile → Multi-Factor Scoring → Ranked Results
```

**Tool:** `rank_restaurants_by_profile(candidates, user_profile, top_n=5)`

**Scoring Formula:**
```
Final Score = (0.35 × Similarity) + (0.25 × Rating) + (0.25 × Attributes) + (0.15 × Distance)
```

**Scoring Components:**

| Factor | Weight | Description |
|--------|--------|-------------|
| **Similarity** | 35% | Vector embedding match from Pinecone (cosine similarity) |
| **Rating** | 25% | Bayesian average: (R×v + C×m)/(v+m) where R=rating, v=review count, C=4.0, m=10 |
| **Attributes** | 25% | Cuisine match, price match, dietary compatibility, style match |
| **Distance** | 15% | Proximity using exponential decay: e^(-distance/2km) |

### Step 4 (Optional): Hard Filtering

```
Candidates → Filter by Requirements → Reduced Set
```

**Tool:** `filter_by_attributes(candidates, required_attributes)`

**Supported filters:**
- `min_rating`: e.g., 4.0
- `max_price`: e.g., "PRICE_LEVEL_MODERATE"
- `required_types`: e.g., ["thai_restaurant"]
- `exclude_types`: e.g., ["fast_food"]
- `open_now`: boolean

## Output Format

The agent returns **formatted text** (not JSON) to the supervisor:

```
🎯 TOP RECOMMENDATIONS FOR USER

Based on preferences: Malaysian street food, casual dining, mid-price
Total candidates analyzed: 20
Top 5 recommendations:

1. Eem - Thai BBQ & Cocktails
   📍 Address: 3808 N Williams Ave #127, Portland, OR 97227, USA
   ⭐ Rating: 4.5 (234 reviews)
   💰 Price: MODERATE
   🎨 Type: Thai, Bar
   📊 Match Score: 0.8542 / 1.0
   💡 Why: Strong cuisine match (Thai/Asian), excellent ratings, moderate price matches budget

2. Por Qué No?
   📍 Address: 3524 N Mississippi Ave, Portland, OR 97227, USA
   ⭐ Rating: 4.3 (189 reviews)
   💰 Price: INEXPENSIVE
   🎨 Type: Mexican, Street Food
   📊 Match Score: 0.7821 / 1.0
   💡 Why: Street food style match, budget-friendly, high similarity to preferences
...
```

## Usage Examples

### Example 1: Quick Recommendations (No User Profile)

**Supervisor sends:**
```
Place data: [/* restaurant objects from places_agent */]
User profile: {} (empty)
```

**Agent workflow:**
1. Process places → Neo4j + Pinecone
2. Use generic query: "popular restaurants"
3. Rank by rating + distance only
4. Return top 5

### Example 2: Personalized Recommendations

**Supervisor sends:**
```
Place data: [/* restaurant objects */]
User profile: {
  "keywords": ["Japanese", "ramen", "authentic"],
  "attributes": {
    "region": ["Japanese"],
    "price_band": "mid"
  }
}
```

**Agent workflow:**
1. Process places → Knowledge graph
2. Query: "authentic Japanese ramen restaurants"
3. Rank with full scoring (similarity + rating + attributes + distance)
4. Return top 5 matching Japanese/ramen preferences

### Example 3: Filtered Recommendations

**Supervisor sends:**
```
Place data: [/* restaurant objects */]
User profile: {/* preferences */}
Hard requirements: {
  "min_rating": 4.0,
  "max_price": "PRICE_LEVEL_MODERATE",
  "required_types": ["vegetarian_restaurant"]
}
```

**Agent workflow:**
1. Process places
2. Filter: rating ≥ 4.0, price ≤ MODERATE, has vegetarian tag
3. Query similar with user preferences
4. Rank filtered candidates
5. Return top 5

## API Integration

### From Supervisor

When routing to `rag_recommender_agent`, the supervisor should include:

```python
# Handoff message format
{
  "role": "assistant",
  "content": "Processing recommendation request. Place data and user profile forwarded.",
  "tool_calls": [{
    "function": {
      "name": "transfer_to_rag_recommender_agent",
      "arguments": {
        "places_data": "[/* JSON string from places_agent */]",
        "user_profile": "{/* JSON object from user_profile_agent */}"
      }
    }
  }]
}
```

### From Frontend/Client

**Request:**
```http
POST /runs/stream
Content-Type: application/json

{
  "assistant_id": "agent",
  "input": {
    "messages": [{
      "role": "user",
      "content": "Find me top 5 Malaysian restaurants in Portland, vegetarian-friendly, mid-price range"
    }]
  }
}
```

**Expected Flow:**
1. Supervisor → `places_agent` (search Portland Malaysian restaurants)
2. Supervisor → `user_profile_agent` (optional, extract preferences)
3. Supervisor → `rag_recommender_agent` (process + rank + recommend)
4. Supervisor → `summarizer_agent` (polish final response)
5. Return to user

## Technical Details

### Dependencies

- **Neo4j**: Knowledge graph storage (nodes: Places, Reviews; relationships: REVIEWS)
- **Pinecone**: Vector database (index: `places-index`, metric: cosine, dimension: 1536)
- **OpenAI**: Embeddings model `text-embedding-3-small`

### Environment Variables

Required in `.env`:
```bash
NEO4J_URI=bolt+ssc://your-instance.databases.neo4j.io
NEO4J_PASSWORD=your-password
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-east-1-aws
OPENAI_API_KEY=your-api-key
```

### Performance

- **Embedding time**: ~100-200ms per place (OpenAI API)
- **Vector search**: ~50-100ms (Pinecone query)
- **Ranking**: ~10-20ms (local computation)
- **Total pipeline**: ~500ms-1s for 10-20 places

## Migration Notes

### From Old Architecture

If you were using separate `rag_agent` and `recommender_agent`:

**OLD:**
```python
workflow = create_supervisor(
    agents=[places, rag, recommender, summarizer],
    ...
)
```

**NEW:**
```python
workflow = create_supervisor(
    agents=[places, rag_recommender, summarizer],
    ...
)
```

**Benefits:**
- ✅ Single agent call instead of two
- ✅ Reduced message passing overhead
- ✅ Unified prompt for better context
- ✅ Simpler supervisor routing logic

### Backward Compatibility

The old `rag_agent.py` and `recommender_agent.py` files are still present but unused. You can keep them for reference or testing.

## Troubleshooting

### Issue: "Place data missing"

**Solution:** Ensure `places_agent` runs first and conversation history contains place results

### Issue: "No results found"

**Possible causes:**
1. No places in Pinecone index → Check if `process_places_data` was called
2. Query too specific → Broaden search terms
3. Hard filters too strict → Relax `filter_by_attributes` requirements

### Issue: "Low match scores"

**Possible causes:**
1. User profile doesn't match available cuisines → Return top results with explanation
2. No user profile provided → Scores rely only on rating + distance
3. Missing metadata in place data → Add `types`, `priceLevel` fields

## Future Enhancements

Potential improvements:
- [ ] Add time-based filtering (open hours, peak times)
- [ ] Include user location for better distance scoring
- [ ] Support dietary restrictions with more granularity
- [ ] Add collaborative filtering (similar users liked...)
- [ ] Cache embeddings for frequently queried places
- [ ] Multi-lingual support for international restaurants

## References

- **Architecture**: `whats_eat/agents/rag_recommender_agent.py`
- **RAG Tools**: `whats_eat/tools/RAG.py`
- **Ranking Tools**: `whats_eat/tools/ranking.py`
- **Test Data**: `tests/place_test.json`, `tests/user_profile_example.json`
- **Supervisor**: `whats_eat/app/supervisor_app.py`
