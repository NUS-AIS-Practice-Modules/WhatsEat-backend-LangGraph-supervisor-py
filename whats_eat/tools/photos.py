from __future__ import annotations
import time
from typing import Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import requests
from ..config import (
    GOOGLE_MAPS_API_KEY, 
    MAX_RETRIES,
    TIMEOUT_SEC,
    BACKOFF_BASE_SEC
)

class PhotoInput(BaseModel):
    photo_reference: str
    max_w: int = Field(800, ge=1, le=1600)
    max_h: int = Field(800, ge=1, le=1600)

@tool("fetch_place_photos", args_schema=PhotoInput)
def fetch_place_photos(photo_reference: str, max_w: int = 800, max_h: int = 800) -> Dict[str, str]:
    """
    Fetch place photo URL from Google Places Photo API.
    Returns the CDN URL for the photo.
    """
    assert GOOGLE_MAPS_API_KEY, "Missing GOOGLE_MAPS_API_KEY"
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "photoreference": photo_reference, 
        "maxwidth": max_w, 
        "maxheight": max_h, 
        "key": GOOGLE_MAPS_API_KEY
    }

    for t in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, allow_redirects=False, timeout=TIMEOUT_SEC)
            if resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(BACKOFF_BASE_SEC ** t)
                continue
            final_url = resp.headers.get("Location") or resp.url
            return {"photo_url": final_url}
        except requests.exceptions.RequestException:
            if t == MAX_RETRIES - 1:
                raise
            time.sleep(BACKOFF_BASE_SEC ** t)
    raise RuntimeError("All retries failed")