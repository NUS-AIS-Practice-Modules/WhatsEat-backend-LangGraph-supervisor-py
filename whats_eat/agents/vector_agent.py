from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional, Any

from whats_eat.app.env_loader import load_env
from sentence_transformers import SentenceTransformer

# Load environment variables including .env.json
load_env()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorAgent:
    def __init__(self) -> None:
        # Pinecone connection
        self.pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name: str = "places-index"

        # Pinecone runtime handles
        self._pinecone_client = None
        self._pinecone_index = None

        # Embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized Vector agent")
        logger.info(f"Pinecone API key present: {bool(self.pinecone_api_key)}")
        logger.info(f"Pinecone environment: {self.pinecone_environment}")

    def connect_pinecone(self) -> None:
        """Initialize Pinecone"""
        if not self.pinecone_api_key:
            raise ValueError("Missing PINECONE_API_KEY in environment")

        from pinecone import Pinecone
        pc = Pinecone(api_key=self.pinecone_api_key)
        
        self._pinecone_client = pc
        self._pinecone_index = pc.Index(self.index_name)
        logger.info(f"Connected to Pinecone index: {self.index_name}")

    def load_json_data(self, file_path: str) -> Any:
        """Read a JSON file and return parsed data (dict or list)."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize_place(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize incoming place record to expected schema."""
        if not isinstance(raw, dict):
            return None

        if "place_id" in raw and "name" in raw:
            return raw

        # Try test format mapping
        pid = raw.get("id")
        dname = raw.get("displayName") or {}
        name = (dname.get("text") if isinstance(dname, dict) else None) or raw.get("name")
        addr = raw.get("formattedAddress") or raw.get("formatted_address")
        loc = raw.get("location", {})
        lat = loc.get("latitude") if isinstance(loc, dict) else None
        lng = loc.get("longitude") if isinstance(loc, dict) else None
        
        if pid and name:
            return {
                "place_id": pid,
                "name": name,
                "formatted_address": addr or "",
                "location": {"lat": lat, "lng": lng} if lat and lng else None,
                "types": [],
                "rating": 0.0,
            }
        return None

    def create_embeddings(self, place_data: Dict[str, Any]) -> None:
        """Encode a textual representation and upsert into Pinecone."""
        parts: List[str] = [
            str(place_data.get("name", "")),
            str(place_data.get("formatted_address", "")),
        ]
        if place_data.get("location"):
            loc = place_data["location"]
            parts.append(f"Location: {loc.get('lat')}, {loc.get('lng')}")

        text_representation = " ".join(p for p in parts if p).strip()
        embedding = self.model.encode(text_representation)

        if not self._pinecone_index:
            self.connect_pinecone()

        self._pinecone_index.upsert(
            vectors=[
                {
                    "id": place_data["place_id"],
                    "values": embedding.tolist(),
                    "metadata": {
                        "name": place_data.get("name"),
                        "address": place_data.get("formatted_address", ""),
                        "rating": place_data.get("rating", 0.0),
                        "lat": place_data.get("location", {}).get("lat"),
                        "lng": place_data.get("location", {}).get("lng"),
                    },
                }
            ]
        )
        logger.info(f"Vector upserted for place: {place_data.get('name')}")

    def process_places_data(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Process JSON and create vector embeddings in Pinecone."""
        data = self.load_json_data(json_file_path)
        if isinstance(data, dict):
            items = data.get("results", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        normalized: List[Dict[str, Any]] = []
        self.connect_pinecone()
        
        for raw in items:
            doc = self._normalize_place(raw)
            if doc:
                normalized.append(doc)
                self.create_embeddings(doc)
                
        logger.info(f"Processed {len(normalized)} places")
        return normalized

    def query_similar_places(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """Find similar places by text query."""
        query_embedding = self.model.encode(query_text).tolist()
        if not self._pinecone_index:
            self.connect_pinecone()
        
        results = self._pinecone_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results nicely
        places = []
        for match in results.matches:
            places.append({
                "place_id": match.id,
                "score": match.score,
                "name": match.metadata.get("name"),
                "address": match.metadata.get("address"),
                "location": {
                    "lat": match.metadata.get("lat"),
                    "lng": match.metadata.get("lng")
                } if match.metadata.get("lat") and match.metadata.get("lng") else None,
            })
            
        return {
            "query": query_text,
            "places": places
        }


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="VectorAgent",
        description="Process Places-style JSON and store vector embeddings for similarity search",
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to places JSON file to process",
    )
    parser.add_argument(
        "--query",
        help="Optional: Text query to search for similar places after processing",
    )

    args = parser.parse_args()
    agent = VectorAgent()

    if args.json_file:
        processed = agent.process_places_data(args.json_file)
        print("\nProcessed places preview:")
        preview = [
            {
                "place_id": d.get("place_id"),
                "name": d.get("name"),
                "address": d.get("formatted_address"),
                "location": d.get("location"),
            }
            for d in processed
        ]
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        
        if args.query:
            print(f"\nSearching for: {args.query}")
            results = agent.query_similar_places(args.query)
            print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(
            "No JSON file provided. Example usage:\n"
            "  py -m whats_eat.agents.vector_agent tests\\test.json\n"
            "  py -m whats_eat.agents.vector_agent tests\\test.json --query 'thai food'\n"
        )
        sys.exit(2)