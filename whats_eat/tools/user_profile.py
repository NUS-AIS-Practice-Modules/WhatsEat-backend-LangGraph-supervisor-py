"""
User profile tooling that wraps YouTube Data API access and OpenAI embeddings.

Exposes three LangChain tools:
- yt_list_liked_videos
- yt_list_subscriptions
- embed_user_preferences
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Sequence


from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
MAX_ATTEMPTS = 3
DEFAULT_MAX_RESULTS = 50
SCOPES_ENV = "YOUTUBE_SCOPES"
TOKEN_ENV = "YOUTUBE_TOKEN_PATH"
DEFAULT_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"

try:  # Optional dependencies; tests monkeypatch the YouTube client to avoid importing these.
    from google.auth.exceptions import RefreshError  # type: ignore[import]
except ImportError:

    class RefreshError(Exception):  # type: ignore[override]
        """Fallback when google-auth is not installed."""


try:
    from google.oauth2.credentials import Credentials  # type: ignore[import]
    from google.auth.transport.requests import Request  # type: ignore[import]
except ImportError:  # pragma: no cover - handled by raising at runtime if actually needed
    Credentials = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]


try:
    from googleapiclient.discovery import build  # type: ignore[import]
    from googleapiclient.errors import HttpError  # type: ignore[import]
except ImportError:  # pragma: no cover - handled by raising at runtime if actually needed
    build = None  # type: ignore[assignment]

    class HttpError(Exception):  # type: ignore[override]
        """Lightweight stand-in to simplify testing without google-api-python-client."""

        def __init__(self, resp: Any, content: Any, uri: str | None = None) -> None:
            super().__init__(content)
            self.resp = resp
            self.content = content
            self.uri = uri

        @property
        def status_code(self) -> Optional[int]:
            return getattr(self.resp, "status", None)


def _load_scopes() -> Sequence[str]:
    raw = os.getenv(SCOPES_ENV)
    if not raw:
        return (DEFAULT_SCOPE,)
    scopes = [scope.strip() for scope in raw.split(",") if scope.strip()]
    return scopes or (DEFAULT_SCOPE,)


def _token_path() -> str:
    return os.getenv(TOKEN_ENV, "token.json")


def _ensure_dependencies() -> None:
    if Credentials is None or Request is None:
        raise RuntimeError(
            "google-auth is required. Install google-auth and google-auth-oauthlib to use "
            "the YouTube tools."
        )
    if build is None:
        raise RuntimeError(
            "google-api-python-client is required. Install google-api-python-client to use "
            "the YouTube tools."
        )


@lru_cache(maxsize=64)
def _get_youtube_client_cached(token_path: str, scopes: tuple[str, ...]):
    """Return an authorized YouTube client bound to a specific token+scopes."""
    _ensure_dependencies()
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"OAuth token not found at '{token_path}'. Complete authorization first."
        )

    creds = Credentials.from_authorized_user_file(token_path, list(scopes))  # type: ignore[misc]
    if not creds:
        raise RuntimeError("Unable to load OAuth credentials from token file.")

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())  # type: ignore[misc]
        except RefreshError as exc:
            raise RuntimeError("Failed to refresh YouTube OAuth credentials.") from exc
        with open(token_path, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    if not creds.valid:
        raise RuntimeError("YouTube credentials are not valid and could not be refreshed.")

    return build("youtube", "v3", credentials=creds, cache_discovery=False)  # type: ignore[misc]


def _get_youtube_client():
    """Backward-compatible wrapper using env/defaults."""
    scopes = tuple(_load_scopes())
    token_path = _token_path()
    return _get_youtube_client_cached(token_path, scopes)

def _coerce_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _http_status(err: BaseException) -> Optional[int]:
    for attr in ("status_code", "status"):
        status = getattr(err, attr, None)
        if isinstance(status, int):
            return status

    resp = getattr(err, "resp", None)
    status = getattr(resp, "status", None)
    return status if isinstance(status, int) else None


def _error_payload(err: BaseException) -> Dict[str, Any]:
    status = _http_status(err)
    message = str(err)
    if len(message) > 240:
        message = message[:237] + "..."
    payload: Dict[str, Any] = {"message": message}
    if status is not None:
        payload["status"] = status
    return payload


def _execute_with_retries(request: Any):
    last_error: Optional[BaseException] = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            return request.execute()
        except HttpError as err:  # type: ignore[misc]
            last_error = err
            status = _http_status(err)
            if status in RETRYABLE_STATUS_CODES and attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("Request execution failed unexpectedly.")


def _clamp_max_results(max_results: int) -> int:
    if max_results <= 0:
        return 1
    if max_results > DEFAULT_MAX_RESULTS:
        return DEFAULT_MAX_RESULTS
    return max_results


def _subscription_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        snippet = item.get("snippet", {})
        resource = snippet.get("resourceId", {})
        channel_id = resource.get("channelId")
        if not channel_id:
            continue
        rows.append(
            {
                "channel_id": channel_id,
                "channel_title": snippet.get("title"),
                "subscribed_at": snippet.get("publishedAt"),
            }
        )
    return rows


def _liked_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        rows.append(
            {
                "video_id": item.get("id"),
                "title": snippet.get("title"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "duration": item.get("contentDetails", {}).get("duration"),
                "view_count": _coerce_int(statistics.get("viewCount")),
                "like_count": _coerce_int(statistics.get("likeCount")),
            }
        )
    return rows


def _empty_result(error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {"items": [], "next_page_token": None}
    if error:
        result["error"] = error
    return result


@tool("yt_list_subscriptions")
def yt_list_subscriptions(
    max_results: int = DEFAULT_MAX_RESULTS,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the user's subscribed channels (channel_id, title, subscribed_at)."""
    service = _get_youtube_client()
    request = (
        service.subscriptions()  # type: ignore[no-untyped-call]
        .list(
            part="snippet",
            mine=True,
            maxResults=_clamp_max_results(max_results),
            pageToken=page_token,
            fields="nextPageToken,items(snippet(title,publishedAt,resourceId/channelId))",
        )
    )
    try:
        response = _execute_with_retries(request)
    except HttpError as err:  # type: ignore[misc]
        status = _http_status(err)
        if status in RETRYABLE_STATUS_CODES:
            return _empty_result(_error_payload(err))
        raise

    return {
        "items": _subscription_rows(response.get("items", [])),
        "next_page_token": response.get("nextPageToken"),
    }


@tool("yt_list_liked_videos")
def yt_list_liked_videos(
    max_results: int = DEFAULT_MAX_RESULTS,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the user's liked videos (video_id, title, channel_title, published_at, duration)."""
    service = _get_youtube_client()
    request = (
        service.videos()  # type: ignore[no-untyped-call]
        .list(
            part="id,snippet,contentDetails,statistics",
            myRating="like",
            maxResults=_clamp_max_results(max_results),
            pageToken=page_token,
            fields=(
                "nextPageToken,items("
                "id,snippet(title,channelTitle,publishedAt),"
                "contentDetails(duration),statistics(viewCount,likeCount)"
                ")"
            ),
        )
    )

    try:
        response = _execute_with_retries(request)
    except HttpError as err:  # type: ignore[misc]
        status = _http_status(err)
        if status in RETRYABLE_STATUS_CODES:
            return _empty_result(_error_payload(err))
        raise

    return {
        "items": _liked_rows(response.get("items", [])),
        "next_page_token": response.get("nextPageToken"),
    }


class EmbedInput(BaseModel):
    text: str = Field(..., description="Text to embed. Concise bullet-style summary is recommended.")
    model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model identifier (e.g., text-embedding-3-small / text-embedding-3-large).",
    )
    normalize: bool = Field(
        default=True,
        description="If true, L2-normalize the output vector (recommended for cosine/dot retrieval).",
    )
    max_chars: Optional[int] = Field(
        default=8000,
        description="Optional hard cap to avoid extremely long inputs; set None to skip.",
    )


@lru_cache(maxsize=4)
def _get_embedder(model: str) -> OpenAIEmbeddings:
    # langchain-openai reads OPENAI_API_KEY from env
    return OpenAIEmbeddings(model=model)


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec] if norm > 0 else vec


@tool("embed_user_preferences", args_schema=EmbedInput)
def embed_user_preferences(
    text: str,
    model: str = "text-embedding-3-small",
    normalize: bool = True,
    max_chars: Optional[int] = 8000,
) -> Dict[str, Any]:
    """
    Return an OpenAI embedding vector for the supplied text.

    Returns:
      {
        "model": str,
        "embedding": List[float],
        "dim": int,
        "normalized": bool,
        "error": str | None
      }
    Never raises: on failure returns {"error": "...", "embedding": []}.
    """
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "model": model,
                "embedding": [],
                "dim": 0,
                "normalized": False,
                "error": "missing_openai_api_key",
            }

        if not isinstance(text, str):
            return {
                "model": model,
                "embedding": [],
                "dim": 0,
                "normalized": False,
                "error": "invalid_text_type",
            }

        clean = text.strip()
        if not clean:
            return {
                "model": model,
                "embedding": [],
                "dim": 0,
                "normalized": False,
                "error": "empty_text",
            }

        if isinstance(max_chars, int) and max_chars > 0 and len(clean) > max_chars:
            clean = clean[:max_chars]

        embedder = _get_embedder(model)
        vec = embedder.embed_query(clean)

        if not isinstance(vec, list) or not vec:
            return {
                "model": model,
                "embedding": [],
                "dim": 0,
                "normalized": False,
                "error": "empty_embedding",
            }

        if normalize:
            vec = _l2_normalize(vec)

        return {
            "model": model,
            "embedding": vec,
            "dim": len(vec),
            "normalized": bool(normalize),
            "error": None,
        }

    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "model": model,
            "embedding": [],
            "dim": 0,
            "normalized": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


@tool("generate_embedding_profile")
def generate_embedding_profile(
    youtube_data: Dict[str, Any],
    model: str = "text-embedding-3-small",
    normalize: bool = True
) -> Dict[str, Any]:
    """
    Generate embedding from YouTube profile data (long-term taste preferences).
    
    Args:
        youtube_data: Dictionary with keys 'liked_videos', 'subscriptions', 'keywords'
        model: OpenAI embedding model to use
        normalize: Whether to L2-normalize the resulting vector
    
    Returns:
        Dictionary with model, embedding, dim, normalized, error fields
    """
    # Construct profile text from YouTube data
    liked_videos = youtube_data.get('liked_videos', [])
    subscriptions = youtube_data.get('subscriptions', [])
    keywords = youtube_data.get('keywords', [])
    
    profile_text = f"""
User's food preferences based on YouTube activity:

Liked videos: {', '.join(liked_videos) if liked_videos else 'None'}

Subscribed channels: {', '.join(subscriptions) if subscriptions else 'None'}

Key interests: {', '.join(keywords) if keywords else 'None'}

Summary: User shows preferences for various cuisines and dining styles based on their YouTube engagement.
    """.strip()
    
    # Use the existing embed_user_preferences function
    result = embed_user_preferences.invoke({
        "text": profile_text,
        "model": model,
        "normalize": normalize
    })
    
    return result


@tool("generate_embedding_intent")
def generate_embedding_intent(
    user_input: Dict[str, Any],
    model: str = "text-embedding-3-small",
    normalize: bool = True
) -> Dict[str, Any]:
    """
    Generate embedding from current user intent (short-term dining request).
    
    Args:
        user_input: Dictionary with budget, location, party_size, dietary_restrictions, 
                   preferences, occasion, time
        model: OpenAI embedding model to use
        normalize: Whether to L2-normalize the resulting vector
    
    Returns:
        Dictionary with model, embedding, dim, normalized, error fields
    """
    # Construct intent text from user input
    budget = user_input.get('budget', 'not specified')
    location = user_input.get('location', 'not specified')
    party_size = user_input.get('party_size', 'not specified')
    dietary_restrictions = user_input.get('dietary_restrictions', [])
    preferences = user_input.get('preferences', 'not specified')
    occasion = user_input.get('occasion', 'casual dining')
    time = user_input.get('time', 'not specified')
    
    intent_text = f"""
Current dining request:
Budget: {budget}
Location: {location}
Party size: {party_size} people
Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
Preferences: {preferences}
Occasion: {occasion}
Time: {time}
    """.strip()
    
    # Use the existing embed_user_preferences function
    result = embed_user_preferences.invoke({
        "text": intent_text,
        "model": model,
        "normalize": normalize
    })
    
    return result


@tool("fuse_embeddings")
def fuse_embeddings(
    profile_embedding: List[float],
    intent_embedding: List[float],
    alpha: float = 0.5
) -> Dict[str, Any]:
    """
    Fuse profile and intent embeddings with alpha weighting.
    
    Args:
        profile_embedding: Long-term taste embedding vector
        intent_embedding: Current intent embedding vector
        alpha: Weight for profile (0-1), (1-alpha) will be weight for intent
               Default 0.5 = equal weighting
    
    Returns:
        Dictionary with fused embedding, dim, alpha, error fields
    """
    try:
        # Validate inputs
        if not profile_embedding or not intent_embedding:
            return {
                "embedding": [],
                "dim": 0,
                "alpha": alpha,
                "error": "One or both embeddings are empty"
            }
        
        if len(profile_embedding) != len(intent_embedding):
            return {
                "embedding": [],
                "dim": 0,
                "alpha": alpha,
                "error": f"Dimension mismatch: {len(profile_embedding)} vs {len(intent_embedding)}"
            }
        
        if not (0 <= alpha <= 1):
            return {
                "embedding": [],
                "dim": 0,
                "alpha": alpha,
                "error": f"Alpha must be between 0 and 1, got {alpha}"
            }
        
        # Weighted combination
        fused = [
            alpha * p + (1 - alpha) * i
            for p, i in zip(profile_embedding, intent_embedding)
        ]
        
        # L2 normalize the fused vector
        norm = sum(x * x for x in fused) ** 0.5
        if norm > 0:
            fused = [x / norm for x in fused]
        
        return {
            "embedding": fused,
            "dim": len(fused),
            "alpha": alpha,
            "error": None
        }
    
    except Exception as exc:
        return {
            "embedding": [],
            "dim": 0,
            "alpha": alpha,
            "error": f"{type(exc).__name__}: {exc}"
        }


__all__ = [
    "yt_list_subscriptions",
    "yt_list_liked_videos",
    "embed_user_preferences",
    "generate_embedding_profile",
    "generate_embedding_intent",
    "fuse_embeddings"
]

# === Interactive OAuth bootstrap (optional, run-once helper) ==================
# 安全起见，不在工具调用时自动触发浏览器授权；仅在你显式调用时执行。
import pathlib
import json

CLIENT_SECRET_ENV = "YOUTUBE_CLIENT_SECRET_PATH"  # 可自定义 client_secret.json 路径
DEFAULT_CLIENT_SECRET = "whats_eat/tools/client_secret.json"


def _client_secret_path() -> str:
    return os.getenv(CLIENT_SECRET_ENV, DEFAULT_CLIENT_SECRET)


def init_user_token(scopes: Optional[Sequence[str]] = None, client_secret_path: Optional[str] = None) -> str:
    """
    交互式生成/修复当前用户的 token 文件。
    - 默认只读 YouTube，并自动追加 openid + userinfo.email 以获取邮箱
    - 若设置了 YOUTUBE_TOKEN_PATH 且不是默认 token.json，则优先写到该路径
    - 否则写到 apps/whatseat/data/tokens/<email>.json
    返回写入的 token 绝对路径字符串
    """
    from google_auth_oauthlib.flow import InstalledAppFlow  # 仅此函数需要

    # 1) 作用域：在现有 _load_scopes() 基础上追加获取邮箱所需的 scopes
    base_scopes = list(_load_scopes())  # 通常是 ["https://www.googleapis.com/auth/youtube.readonly"]
    extra_scopes = ["openid", "https://www.googleapis.com/auth/userinfo.email"]
    req_scopes = tuple(dict.fromkeys((scopes or (base_scopes + extra_scopes))))  # 去重保序

    # 2) 读取 client_secret.json
    cs_path = client_secret_path or _client_secret_path()
    if not os.path.exists(cs_path):
        raise FileNotFoundError(f"client_secret.json not found at: {cs_path}")

    # 3) 本地授权（浏览器回跳）
    flow = InstalledAppFlow.from_client_secrets_file(cs_path, list(req_scopes))
    creds = flow.run_local_server(port=0, prompt="consent")

    # 4) 读取授权用户邮箱（失败时容错）
    email: Optional[str] = None
    try:
        from googleapiclient.discovery import build as _gbuild
        oauth2 = _gbuild("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = oauth2.userinfo().get().execute()  # 需要 userinfo.email
        email = (info.get("email") or "").strip().lower() or None
    except Exception:
        email = None  # 邮箱拿不到也不影响后续写文件

    # 5) 决定 token 写入路径
    #    - 若显式设置了 YOUTUBE_TOKEN_PATH 且不是默认 token.json，则用其值
    #    - 否则自动写到 apps/whatseat/data/tokens/<email>.json（拿不到邮箱就回退到默认 _token_path()）
    explicit = os.getenv(TOKEN_ENV)  # YOUTUBE_TOKEN_PATH
    if explicit and explicit not in ("", "token.json"):
        token_path = pathlib.Path(explicit)
        token_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        if email:
            base_dir = pathlib.Path("apps/whatseat/data/tokens")
            base_dir.mkdir(parents=True, exist_ok=True)
            safe_email = email.replace("/", "_")
            token_path = base_dir / f"{safe_email}.json"
        else:
            token_path = pathlib.Path(_token_path())
            token_path.parent.mkdir(parents=True, exist_ok=True)

    # 6) 写入 token
    token_path.write_text(creds.to_json(), encoding="utf-8")

    # 7) 简查并提示
    data = json.loads(token_path.read_text(encoding="utf-8"))
    if not bool(data.get("refresh_token")):
        print("WARN: No refresh_token in token file. Revoke previous grant and re-run if needed.")
    print(f"WROTE {token_path.resolve()}  (user={email or 'unknown'})")
    return str(token_path.resolve())



# --- 小型 CLI：python -m whats_eat.tools.user_profile --init-token ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube OAuth bootstrap & quick checks")
    parser.add_argument("--init-token", action="store_true", help="Run interactive OAuth and write token.json")
    parser.add_argument("--show-token", action="store_true", help="Print token.json basic info and exit")
    parser.add_argument("--client-secret", type=str, default=None, help="Path to client_secret.json (optional)")
    #read user email
    # parser.add_argument("--whoami", action="store_true", help="Print email for current token")
    #read user email

    args = parser.parse_args()

    if args.init_token:
        init_user_token(client_secret_path=args.client_secret)
    elif args.show_token:
        p = pathlib.Path(_token_path())
        if not p.exists():
            print(f"token not found at {_token_path()}")
        else:
            data = json.loads(p.read_text(encoding="utf-8"))
            print(json.dumps({
                "path": str(p.resolve()),
                "have_access_token": bool(data.get("token")),
                "have_refresh_token": bool(data.get("refresh_token")),
                "scopes": data.get("scopes"),
                "expiry": data.get("expiry"),
            }, indent=2))
    #read user email
    #read user email
    else:
        parser.print_help()

