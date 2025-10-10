from __future__ import annotations
import time
from typing import Dict, Any, Optional
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from ..config import (
    GOOGLE_MAPS_API_KEY, 
    MAX_RETRIES,
    TIMEOUT_SEC, 
    BACKOFF_BASE_SEC
)

def _get(url: str, params: dict, tries: int = MAX_RETRIES, timeout: int = TIMEOUT_SEC):
    for t in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(BACKOFF_BASE_SEC ** t)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException:
            if t == tries - 1:
                raise
            time.sleep(BACKOFF_BASE_SEC ** t)
    raise RuntimeError("All retries failed")

class TextSearchInput(BaseModel):
    query: str
    region_code: Optional[str] = None
    location_bias: Optional[str] = Field(None, description="circle:2000@lat,lng")

@tool("place_text_search", args_schema=TextSearchInput)
def place_text_search(query: str, region_code: Optional[str] = None,
                      location_bias: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for places using Google Places Text Search API.
    Returns a minimal projection of place data.
    """
    assert GOOGLE_MAPS_API_KEY, "Missing GOOGLE_MAPS_API_KEY"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": GOOGLE_MAPS_API_KEY}
    if region_code: params["region"] = region_code
    if location_bias: params["locationbias"] = location_bias
    r = _get(url, params)
    data = r.json()
    items = []
    for it in data.get("results", [])[:25]:
        items.append({
            "place_id": it.get("place_id"),
            "name": it.get("name"),
            "address": it.get("formatted_address"),
            "location": it.get("geometry", {}).get("location"),
            "price_level": it.get("price_level"),
            "rating": it.get("rating"),
            "user_ratings_total": it.get("user_ratings_total"),
            "types": it.get("types", []),
            "photo_refs": [p.get("photo_reference") for p in it.get("photos", [])] if it.get("photos") else []
        })
    return {"candidates": items}

class DetailsBatchInput(BaseModel):
    place_ids: list[str]

@tool("place_details_batch", args_schema=DetailsBatchInput)
def place_details_batch(place_ids: list[str]) -> list[Dict[str, Any]]:
    """
    Batch fetch place details for a list of place IDs.
    Returns minimal projections with only needed fields.
    """
    assert GOOGLE_MAPS_API_KEY, "Missing GOOGLE_MAPS_API_KEY"
    out = []
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    fields = "place_id,name,formatted_address,geometry,opening_hours,website,international_phone_number,rating,user_ratings_total,photos,price_level,types"
    for pid in place_ids:
        r = _get(url, {"place_id": pid, "key": GOOGLE_MAPS_API_KEY, "fields": fields})
        res = r.json().get("result", {})
        if res:
            out.append({
                "place_id": res.get("place_id"),
                "name": res.get("name"),
                "address": res.get("formatted_address"),
                "location": res.get("geometry", {}).get("location"),
                "website": res.get("website"),
                "phone": res.get("international_phone_number"),
                "opening_hours": res.get("opening_hours"),
                "types": res.get("types", []),
                "price_level": res.get("price_level"),
                "rating": res.get("rating"),
                "photos": [p.get("photo_reference") for p in res.get("photos", [])]
            })
    return out

class DeeplinkInput(BaseModel):
    place_id: str
    mode: str = "driving"
    origin: Optional[str] = None

@tool("build_gmaps_deeplink", args_schema=DeeplinkInput)
def build_gmaps_deeplink(place_id: str, mode: str = "driving", origin: Optional[str] = None) -> str:
    """Build a Google Maps deeplink for navigation to a place."""
    base = "https://www.google.com/maps/dir/?api=1"
    dest = f"destination_place_id={place_id}"
    mode_q = f"&travelmode={mode}"
    ori_q = f"&origin={origin}" if origin else ""
    return f"{base}&{dest}{mode_q}{ori_q}"