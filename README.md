# 🤖 WhatsEat LangGraph Supervisor

WhatsEat is a LangGraph-based multi-agent backend that plans and executes a full restaurant discovery pipeline.
A supervisor graph coordinates specialized agents that talk to Google Maps, YouTube, Neo4j, Pinecone, and OpenAI
tools before handing the final payload to the UI. The repository also packages the generic `create_supervisor`
helpers so you can build your own managed agent teams on top of LangGraph.

![Supervisor Architecture](static/img/supervisor.png)

## Key capabilities

- **Orchestrated agent workflow** – `build_app()` assembles Places search, YouTube profile, RAG recommender, and
  summarizer agents, then compiles them into the LangGraph application exported through `langgraph.json` for
  LangGraph Server or CLI usage.
- **Reusable supervisor tooling** – The `whats_eat.langgraph_supervisor` package extends LangGraph’s prebuilt
  supervisor with opinionated handoff tools, agent-name exposure, and configurable output modes, and can be used in
  your own projects via a normal Python import.【
- **Rich restaurant data ingest** – Places tools wrap Google’s REST APIs with retry/backoff, geocoding, and inline
  photo resolution so every card arrives with lat/lng, metadata, and HTTPS photo URLs.
- **Taste-aware recommendations** – A RAG+ranking agent builds a knowledge graph in Neo4j, pushes embeddings to
  Pinecone, and scores restaurants against the user’s embedding profile before the summarizer produces UI-ready JSON.

## Repository layout

| Path | Description |
| --- | --- |
| `whats_eat/app/` | LangGraph entrypoints (`build_app`, compiled `app`) consumed by LangGraph Server and the CLI. 
| `whats_eat/agents/` | REACT-style agents for Places, YouTube profile, RAG recommender, summarizer, routing, and RAG experiments. 
| `whats_eat/tools/` | Stateless tools (Google Places, user profile, ranking, route maps, RAG integrations).
| `whats_eat/configuration/` | Environment loader, config helpers, OAuth bootstrap for Google APIs. 
| `tests/` | Pytest coverage for the supervisor core, agent naming utilities, RAG tools, and reporting helpers.
| `examples/` | Sample place, profile, and summarizer payloads for manual testing of the pipeline.
| `static/` | Architecture diagrams referenced by the documentation.
## Multi-agent architecture

1. **Parallel discovery** – The supervisor first dispatches `places_agent` and `user_profile_agent` in a single
   parallel tool call. Places returns ≥10 candidates with normalized coordinates and photos; the profile agent
   synthesizes cuisine keywords plus a single embedding vector from YouTube subscriptions and likes.
2. **Retrieval-augmented ranking** – Their outputs are paired as `(json1, json2)` and forwarded to
   `rag_recommender_agent`, which writes the data to Neo4j, indexes embeddings in Pinecone, optionally filters by
   hard constraints, and scores the top restaurants across similarity, rating, attribute fit, and distance.
3. **Presentation** – The summarizer agent converts the ranked list into `{ "cards": [...], "rationale": "..." }`
   with structured photo arrays that the Generative UI can render directly.
4. **Optional handoffs** – Built-in forward tools let the supervisor echo an agent’s raw reply back to the user when
   troubleshooting, while all transfers are tracked for observability.

## Requirements

- Python **3.11+** (tooling pins to `>=3.11` in `pyproject.toml`).
- Access to external services depending on the agents you enable:
  - `OPENAI_API_KEY` for chat/embedding models (supervisor, profile embedding, RAG ingest).
  - `GOOGLE_MAPS_API_KEY` for Places and Geocoding tools.
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` plus `PINECONE_*` keys for the RAG recommender (optional if you skip that agent).
  - Optional `YOUTUBE_API_KEY` and OAuth credentials if you want live YouTube scraping via the profile tools.

The environment loader automatically prefers a repository-level `.env.json` before falling back to `.env`, so you can
commit secrets-free templates and load local overrides.

## Installation

```bash
pip install uv  # optional, for dependency management
uv sync          # or: pip install -r requirements.txt
```

> Tip: The project ships an `uv.lock` file for reproducible environments.

## Running the supervisor locally

1. Export or define the required environment variables (see above) in `.env.json` or `.env`.
2. Start the LangGraph development server:

   ```bash
   uv run langgraph dev
   ```

   The CLI reads `langgraph.json` to locate the compiled app in `whats_eat/app/run.py` and host it on
   `http://localhost:2024` by default.
3. Interact with the graph via the LangGraph UI, SDK, or HTTP API to drive the recommendation workflow.

If you only need the compiled graph for deployment, import `build_app()` and serve the resulting
`StateGraph` in your preferred hosting environment.

## Sample data

The `examples/` folder provides ready-made payloads for smoke testing individual agents or seeding the RAG pipeline.
Pair `place_test.json` with `user_profile_example.json` to emulate the supervisor’s `(json1, json2)` handoff, or compare
your UI renderer with `summarizer_output.json` to validate formatting.

## Troubleshooting tips

- Missing API keys raise descriptive `RuntimeError`s—check the `.env` loader order if overrides do not apply.
- Pinecone SDK mismatches (legacy vs. new client) surface actionable guidance from the RAG tools; uninstall the legacy
  `pinecone-client` if you see compatibility errors.
- When experimenting with new agents, ensure you compile them with explicit names; the supervisor validates uniqueness
  before building the graph.

Happy routing!

