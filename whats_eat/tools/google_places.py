from __future__ import annotations

import os
import time
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence

import requests
from langchain_core.tools import tool

_PLACES_BASE_URL = "https://places.googleapis.com/v1"
_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_RETRY_STATUS = {429, 500, 502, 503, 504}

_INLINE_PHOTO_LIMIT = 3
_INLINE_PHOTO_MAX_W = 640
_INLINE_PHOTO_MAX_H = 480

_LOGGER = logging.getLogger(__name__)


def _require_api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GOOGLE_MAPS_API_KEY environment variable for Google Places API access")
    return key


def _request_with_backoff(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    tries: int = 3,
    timeout: int = 20,
) -> requests.Response:
    """Execute an HTTP request with exponential backoff for retryable status codes."""
    last_error: Optional[Exception] = None
    for attempt in range(tries):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            last_error = exc
        else:
            if response.status_code in _RETRY_STATUS and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response
        time.sleep(2 ** attempt)
    if last_error:
        raise RuntimeError(
            f"Failed to call {url}: {last_error}") from last_error
    raise RuntimeError(f"Failed to call {url}")


def _call_places(
    method: str,
    path: str,
    *,
    field_mask: Optional[str],
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wrapper around the Places API handling headers and retries."""
    headers = {"X-Goog-Api-Key": _require_api_key()}
    if field_mask:
        headers["X-Goog-FieldMask"] = field_mask
    response = _request_with_backoff(
        method,
        f"{_PLACES_BASE_URL}{path}",
        headers=headers,
        json_body=json_body,
        params=params,
    )
    if response.headers.get("Content-Type", "").startswith("application/json"):
        return response.json()
    return {"raw": response.content}


def _normalize_place(place: Dict[str, Any]) -> Dict[str, Any]:
    display_name = place.get("displayName") or {}
    location = place.get("location") or {}
    place_id = place.get("id")
    if isinstance(place_id, str) and place_id.startswith("places/"):
        short_id = place_id.split("/", 1)[1]
    else:
        short_id = place_id
    photos = place.get("photos") or []
    photo_names = [
        photo.get("name")
        for photo in photos
        if photo.get("name")
    ][: _INLINE_PHOTO_LIMIT]
    photo_urls = _resolve_photo_urls(photo_names)
    normalized: Dict[str, Any] = {
        "place_id": short_id,
        "raw_place_id": place_id,
        "name": display_name.get("text"),
        "formatted_address": place.get("formattedAddress"),
        "location": (
            {
                "lat": location.get("latitude"),
                "lng": location.get("longitude"),
            }
            if location
            else None
        ),
        "google_maps_uri": place.get("googleMapsUri"),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("userRatingCount") or place.get("userRatingsTotal"),
        "price_level": place.get("priceLevel"),
        "types": place.get("types") or [],
        "photo_names": photo_names,
        "photos": [],
    }
    if photo_urls:
        normalized["photo_urls"] = photo_urls
        normalized["photos"] = [
            {"name": url}
            for url in photo_urls
        ]
    summary = place.get("generativeSummary") or {}
    overview = summary.get("overview") or {}
    if overview.get("text"):
        normalized["summary"] = overview["text"]
    return normalized


def _geocode_address(address: str) -> Dict[str, Any]:
    """Geocode an address into coordinates using Google Geocoding API."""
    if not address:
        raise ValueError("address is required for geocoding")
    params = {"address": address, "key": _require_api_key()}
    resp = _request_with_backoff("GET", _GEOCODE_URL, params=params)
    data = resp.json()
    status = data.get("status")
    if status != "OK":
        raise RuntimeError(f"Geocoding failed: {status} {data.get('error_message')}")
    result = data["results"][0]
    loc = result["geometry"]["location"]
    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted": result.get("formatted_address"),
        "place_id": result.get("place_id"),
        "types": result.get("types") or [],
    }


def _ensure_place_path(place_id: str) -> str:
    return place_id if place_id.startswith("places/") else f"places/{place_id}"


def _fetch_photo_url(photo_name: str, *, max_w: int, max_h: int) -> Optional[str]:
    base_params = {
        "maxWidthPx": max_w,
        "maxHeightPx": max_h,
    }
    last_error: Optional[Exception] = None
    # First attempt with skipHttpRedirect to avoid downloading the full image.
    for extra_params in ({"skipHttpRedirect": "true"}, {}):
        try:
            response = _request_with_backoff(
                "GET",
                f"{_PLACES_BASE_URL}/{photo_name}/media",
                headers={"X-Goog-Api-Key": _require_api_key()},
                params={**base_params, **extra_params},
            )
        except Exception as exc:  # noqa: BLE001 - upstream HTTP client errors
            last_error = exc
            continue

        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                data = response.json()
            except ValueError as exc:  # invalid JSON payload
                last_error = exc
                continue
            photo_uri = data.get("photoUri")
            if photo_uri:
                return photo_uri

        location = response.headers.get("Location")
        if location:
            return location

        # requests follows redirects by default; fall back to the resolved URL.
        if response.url:
            return response.url

    if last_error:
        _LOGGER.warning("Failed to resolve photo %s: %s", photo_name, last_error)
    return None


@lru_cache(maxsize=256)
def _photo_to_url(photo_name: str, max_w: int, max_h: int) -> Optional[str]:
    return _fetch_photo_url(photo_name, max_w=max_w, max_h=max_h)


def _resolve_photo_urls(
    photo_names: Sequence[str],
    *,
    max_count: int = _INLINE_PHOTO_LIMIT,
    max_w: int = _INLINE_PHOTO_MAX_W,
    max_h: int = _INLINE_PHOTO_MAX_H,
) -> List[str]:
    urls: List[str] = []
    for name in list(photo_names)[:max_count]:
        try:
            url = _photo_to_url(name, max_w=max_w, max_h=max_h)
        except Exception:  # network errors should not break the entire place payload
            continue
        if url:
            urls.append(url)
    return urls


@tool("place_geocode")
def place_geocode(address: str) -> Dict[str, Any]:
    """Geocode an address (including postal code) into coordinates using Google Geocoding API.

    This tool converts any address or postal code into latitude and longitude coordinates.
    Returns a dict with: {"lat": ..., "lng": ..., "formatted": ..., "place_id": ..., "types": [...]}

    Requires env GOOGLE_MAPS_API_KEY.
    """
    return _geocode_address(address)


@tool("places_text_search", return_direct=False)
def places_text_search(
    query: str,
    region: str = "SG",
    page_size: int = 20,
    page_limit: int = 3,
) -> Dict[str, Any]:
    """Text search a place on Google Places API (v1).
    - 自动分页：page_size ∈ [1,20]，携带 nextPageToken 连续请求，最多抓取 page_limit 页。
    - 返回字段：用 FieldMask 精确控制。
    """
    page_size = max(1, min(page_size, 20))

    field_mask = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "places.types",
        "places.photos.name",
        "places.generativeSummary",
        "nextPageToken",
    ])

    all_places: List[Dict[str, Any]] = []
    page_token: Optional[str] = None

    for _ in range(max(1, page_limit)):
        payload: Dict[str, Any] = {"textQuery": query, "pageSize": page_size}
        if region:
            payload["regionCode"] = region
        if page_token:
            payload["pageToken"] = page_token

        data = _call_places("POST", "/places:searchText",
                            field_mask=field_mask, json_body=payload)
        batch = [_normalize_place(item) for item in data.get("places", [])]
        all_places.extend(batch)

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        # 官方提示：token 可能需要短暂等待才有效，这里轻微退避
        time.sleep(0.6)

    return {"query": query, "region": region, "candidates": all_places}



@tool("places_coordinate_search", return_direct=False)
def places_coordinate_search(
    latitude: float,
    longitude: float,
    radius: float = 3000.0,
    max_results_per_call: int = 20,
    rank_by: str = "POPULARITY",
    rings: int = 1,
    fans_per_ring: int = 6,
    ring_step_meters: float = 1500.0,
) -> Dict[str, Any]:
    """Nearby search for restaurants using coordinates (Places API v1).
    - 单次调用：使用 searchNearby，maxResultCount 设为 ≤20（更高值不保证放大，实测常≤20）。
    - 扩大范围与数量：可选“扇形多圆扫描”，在中心周围按 rings/fans 扩展多个圆，逐一请求并合并去重。
    - 排序：rankPreference 支持 POPULARITY / DISTANCE。
    - 注意：必须设置 FieldMask（X-Goog-FieldMask）。
    """

    field_mask = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.priceLevel",
        "places.types",
        "places.photos.name",
        "places.generativeSummary",
    ])

    rank_preference = rank_by.upper() if rank_by.upper() in {"POPULARITY", "DISTANCE"} else "POPULARITY"

    def _one_call(lat: float, lng: float, rad: float) -> List[Dict[str, Any]]:
        payload = {
            "includedTypes": ["restaurant"],
            "maxResultCount": max(1, min(int(max_results_per_call), 20)),
            "rankPreference": rank_preference,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(rad)
                }
            }
        }
        data = _call_places("POST", "/places:searchNearby",
                            field_mask=field_mask, json_body=payload)
        return [_normalize_place(item) for item in data.get("places", [])]

    # 先查中心圆
    merged: Dict[str, Dict[str, Any]] = {}
    for item in _one_call(latitude, longitude, radius):
        if item.get("place_id"):
            merged[item["place_id"]] = item

    # 扇形多圆扩展（rings 层，每层 fans_per_ring 个方向）
    # 角度均分；经纬换算：1°纬度≈111_320m；经度需乘 cos(lat)
    import math
    lat_rad = math.radians(latitude)
    meters_per_deg_lat = 111_320.0
    meters_per_deg_lng = meters_per_deg_lat * math.cos(lat_rad)

    def offset_latlng(lat0: float, lng0: float, dx_m: float, dy_m: float) -> (float, float):
        dlat = dy_m / meters_per_deg_lat
        dlng = dx_m / meters_per_deg_lng if meters_per_deg_lng != 0 else 0.0
        return lat0 + dlat, lng0 + dlng

    for r in range(1, max(0, rings) + 1):
        ring_radius_m = r * ring_step_meters
        for k in range(max(1, fans_per_ring)):
            theta = 2 * math.pi * (k / max(1, fans_per_ring))
            dx = ring_radius_m * math.cos(theta)
            dy = ring_radius_m * math.sin(theta)
            lat_i, lng_i = offset_latlng(latitude, longitude, dx, dy)
            # 每个点用同一搜索半径；你也可以按需增大
            batch = _one_call(lat_i, lng_i, radius)
            for item in batch:
                pid = item.get("place_id")
                if pid and pid not in merged:
                    merged[pid] = item

            # 轻微退避，避免 QPS/配额触发
            time.sleep(0.15)

    # 输出
    return {
        "center": {"lat": latitude, "lng": longitude},
        "radius": radius,
        "rank_by": rank_preference,
        "candidates": list(merged.values()),
    }



@tool("places_fetch_photos")
def places_fetch_photos(
    place_id: str,
    max_count: int = _INLINE_PHOTO_LIMIT,
    max_w: int = _INLINE_PHOTO_MAX_W,
    max_h: int = _INLINE_PHOTO_MAX_H,
) -> Dict[str, Any]:
    """Return direct photo URLs and formatted photo objects for a place_id.

    The result includes both the raw URL list (``photo_urls``) and a ``photos``
    array where each entry is ``{"name": "https://..."}``, suitable for the
    frontend carousel.
    """
    field_mask = "photos.name"
    data = _call_places(
        "GET", f"/{_ensure_place_path(place_id)}", field_mask=field_mask)
    photo_entries = data.get("photos", [])
    photo_names = [
        photo.get("name")
        for photo in photo_entries
        if isinstance(photo, dict) and photo.get("name")
    ][: max_count]
    photo_urls = _resolve_photo_urls(
        photo_names,
        max_count=max_count,
        max_w=max_w,
        max_h=max_h,
    )
    return {
        "photo_urls": photo_urls,
        "photos": [
            {"name": url}
            for url in photo_urls
        ],
    }
