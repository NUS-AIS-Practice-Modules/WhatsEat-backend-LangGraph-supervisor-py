# WhatsEat Frontend (Generative UI)

This package provides a React application (bootstrapped with Create React App) that follows the [Generative UI tutorial for LangGraph](https://github.langchain.ac.cn/langgraphjs/cloud/how-tos/generative_ui_react/) and connects to the supervisor workflow defined in `whats_eat/app/supervisor_app.py`.

## Prerequisites

1. Install Node.js 20 or later.
2. Install pnpm, npm, or yarn (examples below use `pnpm`).
3. Copy the backend environment template and fill in your credentials:

   ```bash
   cp ../.env.example ../.env
   ```

4. Run the LangGraph backend locally:

   ```bash
   uv run langgraph dev
   ```

   The command above reads `langgraph.json`, compiles the `agent` graph (defined in `whats_eat/app/run.py`), and exposes it at `http://localhost:2024` by default. Use `--port` if you need a different port.

   > [!TIP]
   > You do not need to edit `langgraph.json`; the default entry already points to the WhatsEat graph.

5. Copy the frontend environment template:

   ```bash
   cp .env.example .env
   ```

   Adjust the values to point to your LangGraph deployment. When using LangGraph Cloud, provide `REACT_APP_LANGGRAPH_API_KEY` and set `REACT_APP_LANGGRAPH_API_URL` to the Cloud endpoint.

## Installation

```bash
cd frontend
pnpm install
```

## Development

```bash
pnpm start
```

Create React App serves the UI at `http://localhost:3000` by default. Update `REACT_APP_LANGGRAPH_API_URL` in `.env` if your backend is reachable at a different host or port (the sample `.env` points to `http://localhost:2024`).

## Production build

```bash
pnpm build
```

The optimized bundle is emitted to `frontend/build`. You can serve it with any static host or integrate it into the backend stack.

## Code structure

- `src/hooks/use_langgraph_chat.ts` encapsulates LangGraph client interactions: thread creation, message persistence, run execution, and structured payload extraction (restaurant cards + rationale).
- `src/components` contains UI primitives adapted from the Generative UI tutorial, extended with WhatsEat-specific affordances.
- Tailwind CSS powers the styling. Update `tailwind.config.js` to customize tokens.

## Connecting to LangGraph Cloud

When deploying to LangGraph Cloud:

1. Create an API key and set it in `.env` (`REACT_APP_LANGGRAPH_API_KEY`).
2. Point `REACT_APP_LANGGRAPH_API_URL` to the Cloud workspace endpoint.
3. Ensure `REACT_APP_LANGGRAPH_GRAPH_ID` matches the graph published from this repository (`agent` by default).

The hook automatically injects the API key into all SDK calls. Streaming runs can be enabled by replacing the `runs.create` + `runs.wait` sequence with `runs.streamEvents` once you are ready to surface token-level updates.
