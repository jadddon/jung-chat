"""Upload to Pinecone - Embeds chunks and uploads to vector database."""

import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from .env.local or .env (check parent dirs too)
load_dotenv("../.env.local")
load_dotenv("../.env")
load_dotenv(".env.local")
load_dotenv(".env")

# Configuration
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX", "jung-works")
EMBEDDING_MODEL = "multilingual-e5-large"
EMBEDDING_DIMS = 1024
BATCH_SIZE = 50  # Reduced to avoid rate limits
MAX_RETRIES = 5


def generate_embeddings(texts: list, retry_count: int = 0) -> list:
    """Generate embeddings using Pinecone's inference API with retry logic."""
    response = requests.post(
        "https://api.pinecone.io/embed",
        headers={
            "Api-Key": PINECONE_API_KEY,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": "2024-10",
        },
        json={
            "model": EMBEDDING_MODEL,
            "inputs": [{"text": t} for t in texts],
            "parameters": {"input_type": "passage", "truncate": "END"},
        },
    )
    if response.status_code == 429 and retry_count < MAX_RETRIES:
        # Rate limited - exponential backoff
        wait_time = 2 ** retry_count * 5  # 5, 10, 20, 40, 80 seconds
        print(f"  Rate limited, waiting {wait_time}s (retry {retry_count + 1}/{MAX_RETRIES})")
        time.sleep(wait_time)
        return generate_embeddings(texts, retry_count + 1)
    if not response.ok:
        raise Exception(f"Embedding API error: {response.status_code} - {response.text}")
    return [item["values"] for item in response.json()["data"]]


def init_pinecone():
    """Initialize Pinecone and create index if needed."""
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    if PINECONE_INDEX not in pc.list_indexes().names():
        print(f"Creating index: {PINECONE_INDEX}")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMS,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        time.sleep(10)

    return pc.Index(PINECONE_INDEX)


def prepare_vectors(chunks: list, embeddings: list) -> list:
    """Prepare vectors with full metadata for Pinecone."""
    vectors = []
    for chunk, emb in zip(chunks, embeddings):
        metadata = {
            "text": chunk["text"][:8000],  # Truncate if needed
            "source_file": chunk["source_file"],
            "work_title": chunk.get("work_title", "Unknown"),
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
        }

        # Add optional metadata
        if chunk.get("chapter"):
            metadata["chapter"] = chunk["chapter"][:200]
        if chunk.get("start_char") is not None:
            metadata["start_char"] = chunk["start_char"]
        if chunk.get("end_char") is not None:
            metadata["end_char"] = chunk["end_char"]

        vectors.append({
            "id": chunk["id"],
            "values": emb,
            "metadata": metadata,
        })
    return vectors


def upload_chunks(chunks_file: str):
    """Upload chunks to Pinecone with full metadata."""
    chunks = json.loads(Path(chunks_file).read_text())
    print(f"Loaded {len(chunks)} chunks from {chunks_file}")

    if not chunks:
        return

    index = init_pinecone()
    total_batches = (len(chunks) - 1) // BATCH_SIZE + 1

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Batch {batch_num}/{total_batches} ({len(batch)} chunks)")

        try:
            embeddings = generate_embeddings([c["text"] for c in batch])
            vectors = prepare_vectors(batch, embeddings)
            index.upsert(vectors=vectors)
            print(f"  Uploaded {len(vectors)} vectors")
        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(1.5)  # Longer delay to avoid rate limits

    print(f"\nUpload complete!")
    print(f"Index stats: {index.describe_index_stats()}")


if __name__ == "__main__":
    upload_chunks(sys.argv[1] if len(sys.argv) > 1 else "chunks/_all_chunks.json")
