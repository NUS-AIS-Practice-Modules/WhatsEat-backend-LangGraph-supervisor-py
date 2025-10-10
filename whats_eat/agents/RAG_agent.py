"""
RAG����?+�""��Z�,�?+Places API���?r,�z,����Y��_+�>_���1�-~�,"�?`��?
"""
import json
import os
from typing import Dict, List
from pathlib import Path
import logging

from whats_eat.app.env_loader import load_env
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import pinecone

# �S�����Z_����?~��?
load_dotenv()

# �.?��r�-���-
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGAgent:
    def __init__(self):
        # Neo4j�.?��r
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_driver = None

        # Pinecone�.?��r
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = "places-index"
        
        # �^?�<�O-sentence transformer�"��z<
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def connect_neo4j(self):
        """��z�Z��^�Neo4j���?r��""""
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD�Z_����?~��?�o��r_��r")
        
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("�^?�SY��z�Z��^�Neo4j���?r��"")
        except Exception as e:
            logger.error(f"��z�Z�Neo4j��'�: {e}")
            raise

    def connect_pinecone(self):
        """��z�Z��^�Pinecone"""
        if not self.pinecone_api_key or not self.pinecone_environment:
            raise ValueError("Pinecone�Z_����?~��?�o��r_��r")
        
        try:
            pinecone.init(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment
            )
            
            # ��,�zo�'����,?�-~�o"�^T�^>���
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=384,  # all-MiniLM-L6-v2�"��z<�s,��'���
                    metric='cosine'
                )
            logger.info("�^?�SY��z�Z��^�Pinecone")
        except Exception as e:
            logger.error(f"��z�Z�Pinecone��'�: {e}")
            raise

    def load_json_data(self, file_path: str) -> Dict:
        """�S����JSON�-؄����?r"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"�S����JSON�-؄���'�: {e}")
            raise

    def create_knowledge_graph(self, place_data: Dict):
        """��+�o��%?���?r�z,����,��Y��_+�>_���"""
        if not self.neo4j_driver:
            raise ValueError("Neo4j��z�Z��o��^?�<�O-")

        try:
            with self.neo4j_driver.session() as session:
                # �^>����o��%?�S,�,1
                session.run("""
                    CREATE (p:Place {
                        place_id: $place_id,
                        name: $name,
                        address: $address,
                        rating: $rating,
                        types: $types
                    })
                """, {
                    'place_id': place_data['place_id'],
                    'name': place_data['name'],
                    'address': place_data.get('formatted_address', ''),
                    'rating': place_data.get('rating', 0.0),
                    'types': place_data.get('types', [])
                })

                # ����S��_,�r��S,�,1�'O�.3�3�
                if 'reviews' in place_data:
                    for review in place_data['reviews']:
                        session.run("""
                            MATCH (p:Place {place_id: $place_id})
                            CREATE (r:Review {
                                author_name: $author_name,
                                rating: $rating,
                                text: $text,
                                time: $time
                            })
                            CREATE (r)-[:REVIEWS]->(p)
                        """, {
                            'place_id': place_data['place_id'],
                            'author_name': review['author_name'],
                            'rating': review['rating'],
                            'text': review['text'],
                            'time': review['time']
                        })

            logger.info(f"�^?�SY�,��o��%? {place_data['name']} �^>����Y��_+�>_���")
        except Exception as e:
            logger.error(f"�^>����Y��_+�>_����'�: {e}")
            raise

    def create_embeddings(self, place_data: Dict):
        """�,��o��%?���?r�^>�����O�.��?`��?"""
        try:
            # �z,����-ؑo���"��
            text_representation = f"{place_data['name']} {place_data.get('formatted_address', '')} "
            text_representation += f"Types: {', '.join(place_data.get('types', []))} "
            
            if 'reviews' in place_data:
                reviews_text = ' '.join([review['text'] for review in place_data['reviews']])
                text_representation += f"Reviews: {reviews_text}"

            # �"Y�^?��O�.��?`��?
            embedding = self.model.encode(text_representation)

            # �-~�,"�^�Pinecone
            index = pinecone.Index(self.index_name)
            index.upsert(
                vectors=[(
                    place_data['place_id'],
                    embedding.tolist(),
                    {
                        'name': place_data['name'],
                        'address': place_data.get('formatted_address', ''),
                        'rating': place_data.get('rating', 0.0)
                    }
                )]
            )
            
            logger.info(f"�^?�SY�,��o��%? {place_data['name']} �^>����'O�-~�,"��O�.��?`��?")
        except Exception as e:
            logger.error(f"�^>�����O�.��?`��?��'�: {e}")
            raise

    def process_places_data(self, json_file_path: str):
        """�,�?+Places API���?r�s,�,��ث��"""
        try:
            # ��z�Z����?r��"
            self.connect_neo4j()
            self.connect_pinecone()

            # �S�������?r
            data = self.load_json_data(json_file_path)
            
            # �,�?+�_?�,��o��%?
            for place in data.get('results', []):
                self.create_knowledge_graph(place)
                self.create_embeddings(place)

            logger.info("�^?�SY�,�?+�%?�o%�o��%?���?r")
        except Exception as e:
            logger.error(f"�,�?+�o��%?���?r��'�: {e}")
            raise
        finally:
            # �.3�--��z�Z�
            if self.neo4j_driver:
                self.neo4j_driver.close()

    def query_similar_places(self, query_text: str, top_k: int = 5):
        """�Y��_��,Z�_"�.��-ؑo��o?�>,����s,�o��%?"""
        try:
            # �"Y�^?�Y��_��-ؑo��s,��O�.��?`��?
            query_embedding = self.model.encode(query_text).tolist()
            
            # �o"Pinecone�,-�?o�'��>,����?`��?
            index = pinecone.Index(self.index_name)
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            return results
        except Exception as e:
            logger.error(f"�Y��_��>,����o��%?��'�: {e}")
            raise

if __name__ == "__main__":
    # CLI: allow running the agent with a JSON file path
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="RAGAgent",
        description="Process Places API JSON and store knowledge graph + embeddings",
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to places JSON file to process (optional).",
    )

    args = parser.parse_args()

    agent = RAGAgent()

    if args.json_file:
        agent.process_places_data(args.json_file)
    else:
        print(
            "No JSON file provided. You can run the module as:\n"
            "  python -m whats_eat.agents.RAG_agent path/to/places.json\n"
            "or:\n"
            "  python whats_eat\\agents\\RAG_agent.py path/to/places.json"
        )
        sys.exit(2)
"""
RAGAgent — Build a simple KG in Neo4j and vector index in Pinecone
from a Google Places-style JSON file, and query for similar places.

Environment variables (loaded via python-dotenv):
- NEO4J_URI (default: bolt://localhost:7687)
- NEO4J_USER (default: neo4j)
- NEO4J_PASSWORD (required)
- PINECONE_API_KEY (required for Pinecone ops)
- PINECONE_ENVIRONMENT (e.g., us-east-1-aws) — used to infer cloud/region

Pinecone SDK support:
- Prefers the new SDK (`pip install pinecone`) with Pinecone/ServerlessSpec
- Falls back to legacy SDK (`pip install pinecone-client`) if present
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer


# Load .env.json or .env if present
load_env(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGAgent:
    def __init__(self) -> None:
        # Neo4j connection
        self.neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password: Optional[str] = os.getenv("NEO4J_PASSWORD")
        self.neo4j_driver = None

        # Pinecone connection
        self.pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name: str = "places-index"

        # Pinecone runtime handles (lazy init) — supports new and legacy SDKs
        self._pinecone_client: Optional[object] = None
        self._pinecone_index: Optional[object] = None
        self._pinecone_new_sdk: bool = False

        # Embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # ----------------------- Neo4j -----------------------
    def connect_neo4j(self) -> None:
        """Connect to Neo4j using environment variables."""
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD is required but missing in environment")
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    # --------------------- Pinecone ----------------------
    def connect_pinecone(self) -> None:
        """Initialize Pinecone, preferring the new SDK and falling back to legacy.

        New SDK usage:
          from pinecone import Pinecone, ServerlessSpec
          pc = Pinecone(api_key=...)
          pc.create_index(..., spec=ServerlessSpec(cloud=..., region=...))
          index = pc.Index(name)

        Legacy SDK usage:
          import pinecone
          pinecone.init(api_key=..., environment=...)
          pinecone.create_index(name, dimension, metric)
          index = pinecone.Index(name)
        """
        if not self.pinecone_api_key:
            raise ValueError("Missing PINECONE_API_KEY in environment")

        # Infer cloud/region from PINECONE_ENVIRONMENT (e.g., us-east-1-aws)
        cloud = "aws"
        region: Optional[str] = None
        if self.pinecone_environment:
            env_l = self.pinecone_environment.lower()
            if env_l.endswith("-aws"):
                cloud, region = "aws", env_l[:-4]
            elif env_l.endswith("-gcp"):
                cloud, region = "gcp", env_l[:-4]
            elif env_l.endswith("-azure"):
                cloud, region = "azure", env_l[:-6]
            else:
                region = env_l

        try:
            # Try new SDK first
            from pinecone import Pinecone as _Pinecone  # type: ignore
            from pinecone import ServerlessSpec as _ServerlessSpec  # type: ignore

            pc = _Pinecone(api_key=self.pinecone_api_key)
            existing = [ix.name for ix in pc.list_indexes()]
            if self.index_name not in existing:
                if not region:
                    region = "us-east-1"
                pc.create_index(
                    name=self.index_name,
                    dimension=384,
                    metric="cosine",
                    spec=_ServerlessSpec(cloud=cloud, region=region),
                )
            self._pinecone_index = pc.Index(self.index_name)
            self._pinecone_client = pc
            self._pinecone_new_sdk = True
            logger.info("Initialized Pinecone (new SDK)")
        except Exception as new_err:
            # Fallback to legacy SDK if available
            try:
                import importlib

                pinecone_legacy = importlib.import_module("pinecone")
                pinecone_legacy.init(
                    api_key=self.pinecone_api_key, environment=self.pinecone_environment
                )
                if self.index_name not in pinecone_legacy.list_indexes():
                    pinecone_legacy.create_index(
                        name=self.index_name, dimension=384, metric="cosine"
                    )
                self._pinecone_index = pinecone_legacy.Index(self.index_name)
                self._pinecone_client = pinecone_legacy
                self._pinecone_new_sdk = False
                logger.info("Initialized Pinecone (legacy SDK)")
            except Exception as legacy_err:
                # Provide a clearer hint if the error likely stems from SDK rename
                msg = str(new_err) if new_err else ""
                if "pinecone-client" in msg or "renamed from `pinecone-client`" in msg:
                    raise RuntimeError(
                        "Pinecone SDK conflict: uninstall 'pinecone-client' and install 'pinecone' (new SDK)."
                    ) from new_err
                raise legacy_err

    # --------------------- Utilities ---------------------
    def load_json_data(self, file_path: str) -> Any:
        """Read a JSON file and return parsed data (dict or list)."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize_place(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize incoming place record to expected schema.

        Supports two formats:
        - Google Places-like: has keys place_id, name, formatted_address, rating, types, reviews
        - Test format (tests/test.json): keys id, displayName.text, formattedAddress
        """
        if not isinstance(raw, dict):
            return None

        if "place_id" in raw and "name" in raw:
            return raw

        # Try test format mapping
        pid = raw.get("id")
        dname = raw.get("displayName") or {}
        name = (dname.get("text") if isinstance(dname, dict) else None) or raw.get("name")
        addr = raw.get("formattedAddress") or raw.get("formatted_address")
        if pid and name:
            return {
                "place_id": pid,
                "name": name,
                "formatted_address": addr or "",
                "types": [],
                "rating": 0.0,
                "reviews": [],
            }
        return None

    # ---------------------- Ingest -----------------------
    def create_knowledge_graph(self, place_data: Dict[str, Any]) -> None:
        """Write place and (optionally) reviews into Neo4j."""
        if not self.neo4j_driver:
            raise ValueError("Neo4j is not connected; call connect_neo4j() first")

        with self.neo4j_driver.session() as session:
            session.run(
                """
                CREATE (p:Place {
                    place_id: $place_id,
                    name: $name,
                    address: $address,
                    rating: $rating,
                    types: $types
                })
                """,
                {
                    "place_id": place_data["place_id"],
                    "name": place_data["name"],
                    "address": place_data.get("formatted_address", ""),
                    "rating": place_data.get("rating", 0.0),
                    "types": place_data.get("types", []),
                },
            )

            if "reviews" in place_data:
                for r in place_data["reviews"]:
                    session.run(
                        """
                        MATCH (p:Place {place_id: $place_id})
                        CREATE (rv:Review {
                            author_name: $author_name,
                            rating: $rating,
                            text: $text,
                            time: $time
                        })
                        CREATE (rv)-[:REVIEWS]->(p)
                        """,
                        {
                            "place_id": place_data["place_id"],
                            "author_name": r.get("author_name"),
                            "rating": r.get("rating"),
                            "text": r.get("text"),
                            "time": r.get("time"),
                        },
                    )

        logger.info(f"KG upserted for place: {place_data.get('name')}")

    def create_embeddings(self, place_data: Dict[str, Any]) -> None:
        """Encode a textual representation and upsert into Pinecone."""
        parts: List[str] = [
            str(place_data.get("name", "")),
            str(place_data.get("formatted_address", "")),
            "Types: " + ", ".join(place_data.get("types", []) or []),
        ]
        if "reviews" in place_data and place_data["reviews"]:
            reviews_text = " ".join(str(rv.get("text", "")) for rv in place_data["reviews"]).strip()
            if reviews_text:
                parts.append("Reviews: " + reviews_text)

        text_representation = " ".join(p for p in parts if p).strip()
        embedding = self.model.encode(text_representation)

        if not self._pinecone_index:
            # Allow implicit init if caller forgot connect_pinecone
            self.connect_pinecone()

        if self._pinecone_new_sdk:
            self._pinecone_index.upsert(
                vectors=[
                    {
                        "id": place_data["place_id"],
                        "values": embedding.tolist(),
                        "metadata": {
                            "name": place_data.get("name"),
                            "address": place_data.get("formatted_address", ""),
                            "rating": place_data.get("rating", 0.0),
                        },
                    }
                ]
            )
        else:
            # Legacy SDK tuple style
            self._pinecone_index.upsert(
                vectors=[
                    (
                        place_data["place_id"],
                        embedding.tolist(),
                        {
                            "name": place_data.get("name"),
                            "address": place_data.get("formatted_address", ""),
                            "rating": place_data.get("rating", 0.0),
                        },
                    )
                ]
            )

        logger.info(f"Vector upserted for place: {place_data.get('name')}")

    def process_places_data(self, json_file_path: str, dry_run: bool = False) -> List[Dict[str, Any]]:
        """End-to-end processing: load JSON, normalize, optionally connect, and upsert.

        Returns the list of normalized place docs processed.
        """
        data = self.load_json_data(json_file_path)
        if isinstance(data, dict):
            items = data.get("results", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        normalized: List[Dict[str, Any]] = []
        for raw in items:
            doc = self._normalize_place(raw)
            if doc:
                normalized.append(doc)

        if not dry_run:
            self.connect_neo4j()
            self.connect_pinecone()
            for place in normalized:
                self.create_knowledge_graph(place)
                self.create_embeddings(place)
            logger.info("Finished processing places JSON: KG + embeddings upserted")
        else:
            logger.info(f"Dry run: would process {len(normalized)} places (no external connections)")

        return normalized

    # ---------------------- Query ------------------------
    def query_similar_places(self, query_text: str, top_k: int = 5) -> Any:
        """Encode the query and perform Pinecone vector search."""
        query_embedding = self.model.encode(query_text).tolist()
        if not self._pinecone_index:
            self.connect_pinecone()
        return self._pinecone_index.query(
            vector=query_embedding, top_k=top_k, include_metadata=True
        )


if __name__ == "__main__":
    # CLI: allow running the agent with a JSON file path
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="RAGAgent",
        description=(
            "Process Places-style JSON and store knowledge graph + embeddings; "
            "then you can query with query_similar_places()."
        ),
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to places JSON file to process (optional)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and normalize only; skip Neo4j/Pinecone connections",
    )

    args = parser.parse_args()
    agent = RAGAgent()

    if args.json_file:
        processed = agent.process_places_data(args.json_file, dry_run=args.dry_run)
        if args.dry_run:
            # Print a compact preview of normalized docs
            preview = [
                {"place_id": d.get("place_id"), "name": d.get("name"), "address": d.get("formatted_address")}
                for d in processed
            ]
            print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(
            "No JSON file provided. You can run the module as:\n"
            "  py -m whats_eat.agents.RAG_agent path\\to\\places.json\n"
            "or:\n"
            "  py whats_eat\\agents\\RAG_agent.py path\\to\\places.json"
        )
        sys.exit(2)
