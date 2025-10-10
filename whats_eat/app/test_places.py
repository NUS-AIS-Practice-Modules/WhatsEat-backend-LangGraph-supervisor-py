"""
Simple offline-friendly test harness for the Places agent/tools.

Usage examples:
- Offline tool-only smoke test:
  py whats_eat\app\test_places.py --offline --query "best ramen near changi"

- Online agent test (requires OPENAI_API_KEY and network):
  py whats_eat\app\test_places.py --query "best ramen near changi with photos"
"""

import argparse
import json
import os
from whats_eat.app.env_loader import load_env

# Load .env.json or .env from repo root
load_env(override=True)


def main():
    parser = argparse.ArgumentParser(prog="test_places_agent")
    parser.add_argument("--query", required=True, help="Natural language request")
    parser.add_argument("--offline", action="store_true", help="Run tools directly, skip LLM")
    args = parser.parse_args()

    if args.offline:
        # Tool-only mode without importing langchain-core
        print("[offline] Simulating places_text_search…")
        ts = {"ok": False, "reason": "not implemented yet", "query": args.query, "region": "SG"}
        print(json.dumps(ts, indent=2))
        print("[offline] Skipping photos (tool not implemented)")
        return

    # Online mode: build agent and invoke a single turn
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Use --offline or set the key to run the agent.")
        raise SystemExit(2)

    # Defer imports so offline path doesn't require langchain/langgraph
    from whats_eat.tools.google_places import places_text_search, places_fetch_photos  # noqa: F401
    from whats_eat.agents.places_agent import build_places_agent
    agent = build_places_agent()
    out = agent.invoke({"messages": [{"role": "user", "content": args.query}]})
    # LangGraph returns a state-like dict; print the last message if present
    msgs = out.get("messages", []) if isinstance(out, dict) else []
    if msgs:
        last = msgs[-1]
        print(last)
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
