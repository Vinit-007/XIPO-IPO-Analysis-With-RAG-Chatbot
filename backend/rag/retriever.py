import os
import json
import faiss
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
BASE_INDEX_PATH = os.path.join(os.path.dirname(__file__), "embeddings", "faiss_index")

# Cache: index_key -> (faiss_index, documents, embedder)
_CACHE = {}


def _index_key_from_json(json_path: str) -> str:
    """
    Derive index folder name from JSON filename.
    Example:
        data/structured.json -> structured
    """
    return os.path.splitext(os.path.basename(json_path))[0].lower()


def retrieve(json_path: str, query: str, top_k: int = 5):
    """
    Retrieve relevant chunks from FAISS index built from the given JSON file.
    """

    index_key = _index_key_from_json(json_path)

    if index_key not in _CACHE:
        index_dir = os.path.join(BASE_INDEX_PATH, index_key)

        index_file = os.path.join(index_dir, "index.faiss")
        docs_file = os.path.join(index_dir, "documents.json")

        if not os.path.exists(index_file):
            raise FileNotFoundError(f"FAISS index not found: {index_file}")

        if not os.path.exists(docs_file):
            raise FileNotFoundError(f"Documents file not found: {docs_file}")

        # Load FAISS index
        index = faiss.read_index(index_file)

        # Load documents
        with open(docs_file, "r", encoding="utf-8") as f:
            documents = json.load(f)

        # Load embedder ONCE
        embedder = SentenceTransformer(MODEL_NAME)

        _CACHE[index_key] = (index, documents, embedder)

    index, documents, embedder = _CACHE[index_key]

    # Encode query
    query_embedding = embedder.encode(
        [query],
        normalize_embeddings=True
    )

    # Search
    _, indices = index.search(query_embedding, top_k)

    # Collect results safely
    results = []
    for idx in indices[0]:
        if 0 <= idx < len(documents):
            results.append(documents[idx])

    return results
