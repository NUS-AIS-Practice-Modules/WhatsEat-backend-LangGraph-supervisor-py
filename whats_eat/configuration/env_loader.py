"""
env_loader: supports loading configuration from either a JSON-style .env.json
at the repo root (object with KEY: VALUE) or a traditional KEY=VALUE .env file.

Preference order: .env.json > .env > existing environment variables.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any


def _repo_root() -> Path:
    # This file is at whats_eat/tools/env_loader.py → root is parents[2]
    return Path(__file__).resolve().parents[2]


def _load_env_json(path: Path, override: bool = True) -> None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            if not isinstance(k, str):
                continue
            val = str(v) if v is not None else ""
            if override or not os.getenv(k):
                os.environ[k] = val
    except Exception:
        # Silent fallback; caller may still attempt .env
        pass


def _load_dotenv(path: Path = None, override: bool = True) -> None:
    from dotenv import load_dotenv
    import os
    if path is not None and path.exists():
        load_dotenv(dotenv_path=str(path), override=override)
    else:
        # Automatically search for a .env file in the current and parent directories
        found = False
        search_path = Path(os.getcwd())
        for parent in [search_path] + list(search_path.parents):
            env_file = parent / ".env"
            if env_file.exists():
                load_dotenv(dotenv_path=str(env_file), override=override)
                found = True
                break
        if not found:
            load_dotenv(override=override)


def load_env(override: bool = True) -> None:
    root = _repo_root()
    env_json = root / ".env.json"
    if env_json.exists():
        _load_env_json(env_json, override=override)
        return
    # Fall back to classic .env
    _load_dotenv(root / ".env", override=override)
