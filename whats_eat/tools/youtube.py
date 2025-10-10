from __future__ import annotations
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from googleapiclient.discovery import build
from ..config import (
    YOUTUBE_API_KEY,
    YOUTUBE_RATE_LIMIT,
    MAX_RETRIES,
    TIMEOUT_SEC
)

class YTProfileInput(BaseModel):
    user_id: Optional[str] = Field(None, description="App user id for OAuth mapping")
    max_items: int = Field(50, ge=1, le=100)

@tool("yt_fetch_history", args_schema=YTProfileInput)
def yt_fetch_history(user_id: Optional[str] = None, max_items: int = 50) -> Dict[str, Any]:
    """
    Fetch user's YouTube watch history.
    Currently using API key only (public data); OAuth to be added.
    """
    assert YOUTUBE_API_KEY, "Missing YOUTUBE_API_KEY"
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    videos = []
    
    try:
        # For demo using search instead of watch history (requires OAuth)
        request = youtube.search().list(
            part="snippet",
            maxResults=min(max_items, 50),
            q="restaurant food review",
            type="video"
        )
        response = request.execute()

        for item in response.get('items', []):
            if item['id']['kind'] == 'youtube#video':
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt']
                }
                videos.append(video_data)
                time.sleep(1.0/YOUTUBE_RATE_LIMIT)  # Rate limiting

        return {"videos": videos}
    except Exception as e:
        return {"error": str(e), "videos": []}

class YTInferInput(BaseModel):
    videos: List[Dict[str, Any]]

@tool("yt_topics_infer", args_schema=YTInferInput)
def yt_topics_infer(videos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze YouTube history to infer food/cuisine preferences.
    Uses basic keyword matching for demo; real impl would use ML.
    """
    cuisine_keywords = {
        'italian': ['pasta', 'pizza', 'italian'],
        'chinese': ['chinese', 'dimsum', 'wonton'],
        'japanese': ['ramen', 'sushi', 'japanese'],
        'mexican': ['taco', 'burrito', 'mexican'],
        'thai': ['thai', 'pad thai', 'curry'],
        'korean': ['korean', 'bbq', 'kbbq', 'bulgogi']
    }

    topic_counts = {}
    cuisine_counts = {}
    channel_counts = {}

    for video in videos:
        title = video['title'].lower()
        desc = video['description'].lower()
        channel = video['channel_title']
        
        # Count channels
        channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        # Count cuisine keywords
        for cuisine, keywords in cuisine_keywords.items():
            for kw in keywords:
                if kw in title or kw in desc:
                    cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
                    break

        # Simple topic extraction from title
        words = title.split()
        for w in words:
            if len(w) > 3:  # Skip short words
                topic_counts[w] = topic_counts.get(w, 0) + 1

    # Sort by frequency
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_cuisines = sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True)
    top_channels = sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "topic_keywords": [t[0] for t in top_topics],
        "cuisine_keywords": [c[0] for c in top_cuisines if c[1] > 0],
        "creators_top": [{"name": c[0], "videos": c[1]} for c in top_channels]
    }