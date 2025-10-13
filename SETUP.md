# WhatsEat Backend - Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation Steps

### 1. Install Core Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

Or install individual packages:

```bash
# LangGraph and LangChain
pip install langgraph>=0.6.0 langchain>=0.3.27 langchain-core>=0.3.40 langchain-openai>=0.3.33

# Database and Vector Store
pip install neo4j>=5.0.0 pinecone-client>=3.0.0

# OpenAI
pip install openai>=1.0.0

# Google APIs
pip install google-api-python-client>=2.0.0 google-auth-httplib2>=0.1.0 google-auth-oauthlib>=1.0.0

# Utilities
pip install requests>=2.31.0

# Testing
pip install pytest>=8.4.1
```

### 2. Environment Configuration

The project uses `whats_eat/.env.json` for environment variables. The file is already configured with:

#### Neo4j Aura Configuration
- **URI**: `neo4j+s://8bc71a15.databases.neo4j.io`
- **Username**: `neo4j`
- **Database**: `neo4j`
- **Instance**: WhatsEat (ID: 8bc71a15)

#### Pinecone Configuration
- **Environment**: `us-east-1-aws`
- **Index**: `places-index`

#### API Keys
- OpenAI API Key (for embeddings and chat models)
- Google Maps API Key (for places search)
- YouTube API Key (for user profile features)

### 3. Verify Installation

Run the test suite to verify everything is set up correctly:

```bash
# Test RAG agent with sample data
python tests/test_rag_agent.py

# Run all tests
pytest tests/
```

## Project Structure

```
WhatsEat-backend-LangGraph-supervisor-py/
├── whats_eat/
│   ├── agents/              # Agent implementations
│   │   ├── RAG_agent.py     # RAG agent using Neo4j + Pinecone
│   │   ├── places_agent.py  # Google Places search
│   │   ├── recommender_agent.py
│   │   ├── route_agent.py
│   │   ├── summarizer_agent.py
│   │   └── user_profile_agent.py
│   ├── tools/               # Tool implementations
│   │   ├── RAG.py          # RAG tools (Neo4j + Pinecone)
│   │   ├── google_places.py
│   │   ├── ranking.py
│   │   ├── route_map.py
│   │   └── user_profile.py
│   ├── app/                # Application layer
│   │   ├── supervisor_app.py
│   │   ├── config.py
│   │   └── env_loader.py
│   └── .env.json           # Environment configuration
├── tests/
│   ├── test_rag_agent.py   # RAG agent tests
│   └── TEST.JSON           # Sample test data
├── pyproject.toml          # Project dependencies
└── README.md
```

## Quick Start

### 1. Process Places Data with RAG Agent

```python
from whats_eat.tools.RAG import process_places_data

# Process test data
result = process_places_data.invoke({
    "json_file_path": "tests/TEST.JSON",
    "dry_run": False  # Set to True to skip external connections
})
```

### 2. Query Similar Places

```python
from whats_eat.tools.RAG import query_similar_places_tool

# Search for similar places
result = query_similar_places_tool.invoke({
    "query_text": "Thai BBQ restaurant",
    "top_k": 5
})
```

### 3. Use the Supervisor System

```python
from whats_eat.app.supervisor_app import build_supervisor

# Build and run the supervisor
supervisor = build_supervisor()
# Use with LangGraph workflow...
```

## Models Used

All agents use **GPT-5-mini** model:
- `places_agent`
- `recommender_agent`
- `route_agent`
- `summarizer_agent`
- `user_profile_agent`
- `rag_agent`
- `supervisor`

## Troubleshooting

### Neo4j Connection Issues
- Ensure you're using the Neo4j Aura URI: `neo4j+s://8bc71a15.databases.neo4j.io`
- Wait 60 seconds after instance creation before connecting
- Verify credentials in `.env.json`

### Pinecone Setup
- Index name: `places-index`
- Dimension: 1536 (for text-embedding-3-small)
- Metric: cosine
- Cloud: AWS, Region: us-east-1

### Missing Dependencies
```bash
# If you get import errors, install the specific package:
pip install <package-name>

# Or reinstall all dependencies:
pip install -r requirements.txt --force-reinstall
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_agent.py

# Run with verbose output
pytest -v
```

### Code Style
```bash
# Format code
ruff format .

# Check linting
ruff check .
```

## License

MIT License
