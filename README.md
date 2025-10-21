# WhatsEat LangGraph Supervisor

WhatsEat is a LangGraph-based multi-agent backend that plans and executes a full restaurant discovery pipeline.
A supervisor graph coordinates specialized agents that talk to Google Maps, YouTube, Neo4j, Pinecone, and OpenAI
tools before handing the final payload to the UI. The repository also packages the generic `create_supervisor`
helpers so you can build your own managed agent teams on top of LangGraph.

![Supervisor Architecture](static/img/supervisor.png)

## Key capabilities

- **Orchestrated agent workflow** – `build_app()` assembles Places search, YouTube profile, RAG recommender, and
  summarizer agents, then compiles them into the LangGraph application exported through `langgraph.json` for
  LangGraph Server or CLI usage.【F:whats_eat/app/supervisor_app.py†L1-L115】【F:whats_eat/app/run.py†L1-L13】【F:langgraph.json†L1-L8】
- **Reusable supervisor tooling** – The `whats_eat.langgraph_supervisor` package extends LangGraph’s prebuilt
  supervisor with opinionated handoff tools, agent-name exposure, and configurable output modes, and can be used in
  your own projects via a normal Python import.【F:whats_eat/langgraph_supervisor/supervisor.py†L1-L238】【F:whats_eat/langgraph_supervisor/__init__.py†L1-L7】
- **Rich restaurant data ingest** – Places tools wrap Google’s REST APIs with retry/backoff, geocoding, and inline
  photo resolution so every card arrives with lat/lng, metadata, and HTTPS photo URLs.【F:whats_eat/tools/google_places.py†L1-L212】
- **Taste-aware recommendations** – A RAG+ranking agent builds a knowledge graph in Neo4j, pushes embeddings to
  Pinecone, and scores restaurants against the user’s embedding profile before the summarizer produces UI-ready JSON.【F:whats_eat/agents/rag_recommender_agent.py†L1-L120】【F:whats_eat/tools/RAG.py†L1-L163】

## Repository layout

| Path | Description |
| --- | --- |
| `whats_eat/app/` | LangGraph entrypoints (`build_app`, compiled `app`) consumed by LangGraph Server and the CLI.【F:whats_eat/app/run.py†L1-L13】 |
| `whats_eat/agents/` | REACT-style agents for Places, YouTube profile, RAG recommender, summarizer, routing, and RAG experiments.【F:whats_eat/agents/places_agent.py†L1-L38】【F:whats_eat/agents/user_profile_agent.py†L1-L54】【F:whats_eat/agents/rag_recommender_agent.py†L1-L120】【F:whats_eat/agents/summarizer_agent.py†L1-L33】 |
| `whats_eat/tools/` | Stateless tools (Google Places, user profile, ranking, route maps, RAG integrations).【F:whats_eat/tools/__init__.py†L1-L3】【F:whats_eat/tools/google_places.py†L1-L212】【F:whats_eat/tools/ranking.py†L1-L200】【F:whats_eat/tools/RAG.py†L1-L163】 |
| `whats_eat/configuration/` | Environment loader, config helpers, OAuth bootstrap for Google APIs.【F:whats_eat/configuration/env_loader.py†L1-L47】 |
| `tests/` | Pytest coverage for the supervisor core, agent naming utilities, RAG tools, and reporting helpers.【F:tests/test_supervisor.py†L1-L120】【F:tests/test_rag_agent.py†L1-L200】 |
| `examples/` | Sample place, profile, and summarizer payloads for manual testing of the pipeline.【F:examples/place_test.json†L1-L200】【F:examples/user_profile_example.json†L1-L160】 |
| `static/` | Architecture diagrams referenced by the documentation.【F:static/img/supervisor.png†L1-L1】 |

## Multi-agent architecture

1. **Parallel discovery** – The supervisor first dispatches `places_agent` and `user_profile_agent` in a single
   parallel tool call. Places returns ≥10 candidates with normalized coordinates and photos; the profile agent
   synthesizes cuisine keywords plus a single embedding vector from YouTube subscriptions and likes.【F:whats_eat/app/supervisor_app.py†L17-L64】【F:whats_eat/agents/places_agent.py†L11-L38】【F:whats_eat/agents/user_profile_agent.py†L13-L54】
2. **Retrieval-augmented ranking** – Their outputs are paired as `(json1, json2)` and forwarded to
   `rag_recommender_agent`, which writes the data to Neo4j, indexes embeddings in Pinecone, optionally filters by
   hard constraints, and scores the top restaurants across similarity, rating, attribute fit, and distance.【F:whats_eat/app/supervisor_app.py†L22-L78】【F:whats_eat/agents/rag_recommender_agent.py†L25-L103】
3. **Presentation** – The summarizer agent converts the ranked list into `{ "cards": [...], "rationale": "..." }`
   with structured photo arrays that the Generative UI can render directly.【F:whats_eat/app/supervisor_app.py†L79-L103】【F:whats_eat/agents/summarizer_agent.py†L9-L33】
4. **Optional handoffs** – Built-in forward tools let the supervisor echo an agent’s raw reply back to the user when
   troubleshooting, while all transfers are tracked for observability.【F:whats_eat/app/supervisor_app.py†L12-L21】【F:whats_eat/langgraph_supervisor/handoff.py†L1-L160】

## Requirements

- Python **3.11+** (tooling pins to `>=3.11` in `pyproject.toml`).【F:pyproject.toml†L1-L43】
- Access to external services depending on the agents you enable:
  - `OPENAI_API_KEY` for chat/embedding models (supervisor, profile embedding, RAG ingest).【F:whats_eat/agents/user_profile_agent.py†L13-L54】【F:whats_eat/tools/RAG.py†L1-L163】
  - `GOOGLE_MAPS_API_KEY` for Places and Geocoding tools.【F:whats_eat/tools/google_places.py†L1-L119】
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` plus `PINECONE_*` keys for the RAG recommender (optional if you skip that agent).【F:whats_eat/tools/RAG.py†L14-L105】
  - Optional `YOUTUBE_API_KEY` and OAuth credentials if you want live YouTube scraping via the profile tools.【F:whats_eat/tools/user_profile.py†L1-L220】

The environment loader automatically prefers a repository-level `.env.json` before falling back to `.env`, so you can
commit secrets-free templates and load local overrides.【F:whats_eat/configuration/env_loader.py†L1-L47】

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
   `http://localhost:2024` by default.【F:langgraph.json†L1-L8】【F:whats_eat/app/run.py†L1-L13】
3. Interact with the graph via the LangGraph UI, SDK, or HTTP API to drive the recommendation workflow.

If you only need the compiled graph for deployment, import `build_app()` and serve the resulting
`StateGraph` in your preferred hosting environment.【F:whats_eat/app/supervisor_app.py†L1-L115】

## Using the supervisor helpers in your own project

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from whats_eat.langgraph_supervisor import create_supervisor

model = ChatOpenAI(model="gpt-4o")
math_agent = create_react_agent(model=model, tools=[], name="math_expert")
research_agent = create_react_agent(model=model, tools=[], name="research_expert")

workflow = create_supervisor(
    [research_agent, math_agent],
    model=model,
    parallel_tool_calls=True,
)
app = workflow.compile()
```

`create_supervisor` exposes the same knobs used by WhatsEat—handoff tool injection, agent name formatting, output
modes, and structured responses—so you can rapidly stand up bespoke teams without reimplementing the plumbing.【F:whats_eat/langgraph_supervisor/supervisor.py†L69-L238】

## Testing & quality

- **Unit tests:** `make test` (runs `uv run pytest -vv --disable-socket --allow-unix-socket`).【F:Makefile†L9-L17】
- **Watch mode:** `make test_watch` for `pytest-watch` with live reloads.【F:Makefile†L9-L17】
- **Linting/formatting:** `make lint` / `make format` executes `ruff` (format + lint) and the `ty` static checker; add
  `*_diff` variants to restrict to changes against `master`.【F:Makefile†L19-L37】

Some tests hit external services; they automatically skip if the necessary credentials are missing, but double-check
before running in CI environments.【F:tests/test_rag_agent.py†L1-L200】

## Sample data

The `examples/` folder provides ready-made payloads for smoke testing individual agents or seeding the RAG pipeline.
Pair `place_test.json` with `user_profile_example.json` to emulate the supervisor’s `(json1, json2)` handoff, or compare
your UI renderer with `summarizer_output.json` to validate formatting.【F:examples/place_test.json†L1-L200】【F:examples/user_profile_example.json†L1-L160】【F:examples/summarizer_output.json†L1-L200】

## Troubleshooting tips

- Missing API keys raise descriptive `RuntimeError`s—check the `.env` loader order if overrides do not apply.【F:whats_eat/tools/google_places.py†L1-L38】【F:whats_eat/configuration/env_loader.py†L1-L47】
- Pinecone SDK mismatches (legacy vs. new client) surface actionable guidance from the RAG tools; uninstall the legacy
  `pinecone-client` if you see compatibility errors.【F:whats_eat/tools/RAG.py†L60-L118】
- When experimenting with new agents, ensure you compile them with explicit names; the supervisor validates uniqueness
  before building the graph.【F:whats_eat/langgraph_supervisor/supervisor.py†L181-L205】

Happy routing!
