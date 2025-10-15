# RAG + Recommender Integration - Change Summary

## Overview

Combined the RAG agent and Recommender agent into a single **RAG Recommender Agent** that handles the complete recommendation pipeline: data ingestion → embedding → similarity search → intelligent ranking → formatted output.

## Files Created

### 1. `whats_eat/agents/rag_recommender_agent.py` ✨ NEW
**Purpose**: Combined agent that integrates RAG and recommendation capabilities

**Key Features**:
- Processes place data and builds Neo4j knowledge graph + Pinecone embeddings
- Performs semantic similarity search using user profile
- Ranks results with multi-factor scoring (similarity 35%, rating 25%, attributes 25%, distance 15%)
- Returns formatted text recommendations to supervisor

**Tools Used**:
- `process_places_data` - Store places in Neo4j + Pinecone
- `query_similar_places_tool` - Vector similarity search
- `rank_restaurants_by_profile` - Multi-factor ranking algorithm
- `filter_by_attributes` - Hard requirement filtering

### 2. `RAG_RECOMMENDER_GUIDE.md` 📚 NEW
**Purpose**: Comprehensive documentation for the new combined agent

**Contents**:
- Input requirements (place data + user profile JSON formats)
- 4-step processing pipeline explanation
- Scoring algorithm details
- Usage examples
- API integration guide
- Troubleshooting tips
- Migration notes from old architecture

### 3. `test_rag_recommender_example.py` 🧪 NEW
**Purpose**: Example script demonstrating the agent workflow

**Features**:
- Loads test data from `tests/place_test.json` and `tests/user_profile_example.json`
- Shows expected supervisor message format
- Demonstrates complete processing flow
- Displays expected output format

## Files Modified

### 1. `whats_eat/app/supervisor_app.py` ✏️ MODIFIED

**Changes**:
```python
# OLD imports
from whats_eat.agents.recommender_agent import build_recommender_agent
from whats_eat.agents.RAG_agent import build_rag_agent

# NEW import
from whats_eat.agents.rag_recommender_agent import build_rag_recommender_agent
```

**Agent list**:
```python
# OLD
agents=[places, user_profile, recommender, summarizer, route, rag]

# NEW
agents=[places, user_profile, rag_recommender, summarizer, route]
```

**Updated supervisor prompt**:
- Removed separate `rag_agent` and `recommender_agent` descriptions
- Added comprehensive `rag_recommender_agent` description
- Updated routing guide for new workflow
- Simplified multi-step handling flows

**Key routing changes**:
- OLD: `places_agent → rag_agent → recommender_agent → summarizer_agent`
- NEW: `places_agent → rag_recommender_agent → summarizer_agent`

### 2. `whats_eat/agents/__init__.py` ✏️ MODIFIED

**Added export**:
```python
from .rag_recommender_agent import build_rag_recommender_agent

__all__ = [
    # ... existing agents ...
    "build_rag_recommender_agent"
]
```

## Architecture Changes

### OLD Architecture (3 agents, 4 steps)
```
User Request
    ↓
Supervisor → places_agent (get restaurants)
    ↓
Supervisor → rag_agent (store in Neo4j + Pinecone)
    ↓
Supervisor → recommender_agent (rank results)
    ↓
Supervisor → summarizer_agent (format response)
    ↓
User Response
```

### NEW Architecture (2 agents, 3 steps) ✨
```
User Request
    ↓
Supervisor → places_agent (get restaurants)
    ↓
Supervisor → rag_recommender_agent (store + search + rank)
    ↓
Supervisor → summarizer_agent (format response)
    ↓
User Response
```

## Benefits

### 1. **Reduced Complexity** 🎯
- **Before**: 6 agents (places, user_profile, rag, recommender, route, summarizer)
- **After**: 5 agents (places, user_profile, rag_recommender, route, summarizer)
- Fewer handoffs = faster processing

### 2. **Better Context** 🧠
- Single agent maintains full context of both place data and user preferences
- No information loss between RAG and ranking steps
- More coherent explanations in output

### 3. **Simplified Routing** 🚦
- Supervisor has fewer decision points
- Clearer workflow patterns
- Easier to debug and monitor

### 4. **Improved Performance** ⚡
- One agent invocation instead of two
- Reduced message passing overhead
- Faster end-to-end response time

### 5. **Unified Prompt** 📝
- Single comprehensive prompt covers entire pipeline
- Better instruction following
- More consistent behavior

## Input Format

The agent expects **TWO JSON datasets** forwarded by supervisor:

### Place Data (from places_agent)
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

### User Profile Data (from user_profile_agent or extracted)
```json
{
  "keywords": ["street food", "Malaysian", "Japanese"],
  "attributes": {
    "style": ["street food", "casual"],
    "region": ["Malaysian", "Japanese", "Chinese"],
    "price_band": "mid",
    "diet": ["vegetarian"]
  },
  "embedding": [/* 1536-dim vector */]
}
```

## Output Format

Returns **formatted text** (not JSON) to supervisor:

```
🎯 TOP RECOMMENDATIONS FOR USER

Based on preferences: street food, Malaysian, Japanese
Total candidates analyzed: 20
Top 5 recommendations:

1. Eem - Thai BBQ & Cocktails
   📍 Address: 3808 N Williams Ave #127, Portland, OR 97227, USA
   ⭐ Rating: 4.5 (234 reviews)
   💰 Price: MODERATE
   🎨 Type: Thai, Bar
   📊 Match Score: 0.8542 / 1.0
   💡 Why: Strong Asian cuisine match, excellent ratings, moderate price

[... 4 more recommendations ...]
```

## Processing Pipeline

### Step 1: Knowledge Base Building
- **Tool**: `process_places_data(places_data=<json_string>)`
- **Actions**: 
  - Store in Neo4j graph (Place nodes, Review relationships)
  - Generate OpenAI embeddings (text-embedding-3-small, 1536 dims)
  - Index vectors in Pinecone

### Step 2: Semantic Search
- **Tool**: `query_similar_places_tool(query=<text>, top_k=20)`
- **Actions**:
  - Convert user preferences to search query
  - Vector similarity search in Pinecone
  - Return candidates with similarity scores

### Step 3: Intelligent Ranking
- **Tool**: `rank_restaurants_by_profile(candidates, user_profile, top_n=5)`
- **Scoring**:
  - **Similarity**: 35% (vector embedding match)
  - **Rating**: 25% (Bayesian average)
  - **Attributes**: 25% (cuisine, price, diet, style match)
  - **Distance**: 15% (proximity with exponential decay)

### Step 4 (Optional): Filtering
- **Tool**: `filter_by_attributes(candidates, required_attributes)`
- **Filters**: min_rating, max_price, required_types, exclude_types, open_now

## Testing

### Run Example Script
```bash
python test_rag_recommender_example.py
```

### Expected Output
Shows the complete workflow with test data from:
- `tests/place_test.json` (4 Portland restaurants)
- `tests/user_profile_example.json` (Malaysian/Japanese street food preferences)

## Migration Notes

### Old Agents Still Present (Unused)
- `whats_eat/agents/RAG_agent.py` - Keep for reference
- `whats_eat/agents/recommender_agent.py` - Keep for reference

These files are **not imported** in `supervisor_app.py` and will not be used.

### To Remove Old Agents (Optional)
If you want to clean up:
```bash
# These files are no longer used
rm whats_eat/agents/RAG_agent.py
rm whats_eat/agents/recommender_agent.py
```

Update `__init__.py` to remove old exports if deleted.

## Dependencies

No new dependencies required! Uses existing:
- `neo4j>=5.0.0`
- `pinecone>=5.0.0` (updated from `pinecone-client`)
- `openai>=1.0.0`
- `langgraph>=0.6.0`

## Environment Variables

Required in `.env`:
```bash
NEO4J_URI=bolt+ssc://your-instance.databases.neo4j.io
NEO4J_PASSWORD=your-password
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-east-1-aws
OPENAI_API_KEY=your-api-key
```

## Next Steps

1. **Test the new agent**:
   ```bash
   python -m uv run langgraph dev
   ```

2. **Send test request** via API:
   ```bash
   curl http://127.0.0.1:2024/runs/stream \
     -H "Content-Type: application/json" \
     -d '{
       "assistant_id": "agent",
       "input": {
         "messages": [{
           "role": "user",
           "content": "Find me top 5 Malaysian restaurants in Portland"
         }]
       }
     }'
   ```

3. **Monitor in LangSmith**:
   - Open: https://smith.langchain.com/
   - Project: `whatseat-dev`
   - Trace the complete workflow

4. **Verify components**:
   - ✅ Neo4j: Check Places nodes created
   - ✅ Pinecone: Verify embeddings indexed
   - ✅ Rankings: Review score breakdowns

## Troubleshooting

### Issue: Agent not found
**Solution**: Restart server to reload agent registry

### Issue: No results returned
**Check**:
1. Place data was processed (check Neo4j)
2. Embeddings were indexed (check Pinecone dashboard)
3. User profile has valid keywords

### Issue: Low match scores
**Possible causes**:
- User preferences don't match available cuisines
- Missing metadata in place data (types, priceLevel)
- No user profile provided (use default scoring)

## Performance Metrics

Expected timings:
- **Embedding generation**: 100-200ms per place
- **Vector search**: 50-100ms
- **Ranking**: 10-20ms
- **Total pipeline**: 500ms-1s for 10-20 places

## References

- **Main agent file**: `whats_eat/agents/rag_recommender_agent.py`
- **Documentation**: `RAG_RECOMMENDER_GUIDE.md`
- **Test script**: `test_rag_recommender_example.py`
- **Tools**: `whats_eat/tools/RAG.py`, `whats_eat/tools/ranking.py`
- **Supervisor**: `whats_eat/app/supervisor_app.py`

---

**Status**: ✅ Complete and Ready for Testing

**Date**: October 15, 2025

**Impact**: High - Simplified architecture with improved performance and maintainability
