"""
Embed Store - FAISS index builder for RAG.

Builds and stores FAISS embeddings for JSON files.
Uses file-based indexing (json_path as source of truth).
"""

import os
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from chunking import load_and_chunk
from index_manager import check_or_register_json, update_registry, get_index_path

# Embedding model
MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Cache for embedder (avoid reloading)
_embedder_cache = None


def _get_embedder():
    """Get or create the sentence transformer embedder."""
    global _embedder_cache
    if _embedder_cache is None:
        print(f"📦 Loading embedding model: {MODEL_NAME}")
        _embedder_cache = SentenceTransformer(MODEL_NAME, device="cpu")
    return _embedder_cache


def build_index(json_path: str) -> str:
    """
    Build FAISS index for a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        Path to the created index directory
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    # Check current status
    action, index_dir = check_or_register_json(json_path)
    
    if action == "load":
        print(f"✅ Index already exists for {os.path.basename(json_path)}, skipping embedding.")
        return index_dir
    
    if action == "rebuild":
        print(f"♻️ Document changed for {os.path.basename(json_path)}, rebuilding index.")
    
    if action == "create":
        print(f"🆕 Creating new index for {os.path.basename(json_path)}")
    
    # Create index directory
    os.makedirs(index_dir, exist_ok=True)
    
    # Get embedder
    embedder = _get_embedder()
    
    # Load and chunk the document
    print(f"📄 Chunking document...")
    documents = load_and_chunk(json_path)
    
    if not documents:
        raise ValueError(f"No content extracted from {json_path}")
    
    print(f"   📊 Created {len(documents)} chunks")
    
    # Extract texts for embedding
    texts = [d["text"] for d in documents]
    
    # Generate embeddings
    print(f"🧮 Generating embeddings...")
    embeddings = embedder.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
        batch_size=8
    )
    
    # Create FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product for normalized vectors
    index.add(np.array(embeddings))
    
    # Save index
    index_file = os.path.join(index_dir, "index.faiss")
    faiss.write_index(index, index_file)
    print(f"💾 Saved FAISS index: {index_file}")
    
    # Save documents with metadata
    docs_file = os.path.join(index_dir, "documents.json")
    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved documents: {docs_file}")
    
    # Update registry
    update_registry(json_path)
    
    print(f"✅ Index ready: {index_dir}")
    return index_dir


def delete_index(json_path: str) -> bool:
    """
    Delete the FAISS index for a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        True if deleted, False if not found
    """
    import shutil
    from index_manager import remove_from_registry
    
    index_dir = get_index_path(json_path)
    
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
        remove_from_registry(json_path)
        print(f"🗑️ Deleted index: {index_dir}")
        return True
    
    return False


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Default test file
    test_json = os.path.join(os.path.dirname(__file__), "data", "structured.json")
    
    if len(sys.argv) > 1:
        test_json = sys.argv[1]
    
    if os.path.exists(test_json):
        print(f"Building index for: {test_json}")
        build_index(test_json)
    else:
        print(f"File not found: {test_json}")
