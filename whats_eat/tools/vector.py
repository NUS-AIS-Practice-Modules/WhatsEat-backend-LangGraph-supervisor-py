from __future__ import annotations
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import pinecone
from sentence_transformers import SentenceTransformer
from ..config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
    EMBEDDING_DIM
)

# Initialize embedding model once
model = SentenceTransformer(EMBEDDING_MODEL)

class VectorUpsertInput(BaseModel):
    place_id: str
    text: str
    metadata: Dict[str, Any]

@tool("vector_embed_and_upsert", args_schema=VectorUpsertInput)
def vector_embed_and_upsert(place_id: str, text: str, metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Compute embeddings and upsert to Pinecone vector store.
    """
    assert PINECONE_API_KEY, "Missing PINECONE_API_KEY"
    
    # Initialize Pinecone
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    index = pinecone.Index(PINECONE_INDEX)
    
    # Generate embedding
    embedding = model.encode(text)
    
    # Upsert to Pinecone
    index.upsert([(place_id, embedding.tolist(), metadata)])
    
    return {"vector_id": place_id}

class VectorSearchInput(BaseModel):
    query: str
    top_k: int = Field(5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None

@tool("vector_search", args_schema=VectorSearchInput)
def vector_search(query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Search vector store using query embedding.
    Returns top_k most similar items.
    """
    assert PINECONE_API_KEY, "Missing PINECONE_API_KEY"
    
    # Initialize Pinecone
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    index = pinecone.Index(PINECONE_INDEX)
    
    # Generate query embedding
    query_embedding = model.encode(query)
    
    # Search with optional filters
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True,
        filter=filters
    )
    
    return results.to_dict()