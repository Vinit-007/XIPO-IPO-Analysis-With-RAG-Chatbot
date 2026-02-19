"""
Index Manager for RAG embeddings.

Manages the registry of indexed JSON files with hash-based change detection.
Uses JSON filename (not company name) as the single source of truth.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Tuple, Optional

# Paths relative to this file's directory
_BASE_DIR = os.path.dirname(__file__)
REGISTRY_PATH = os.path.join(_BASE_DIR, "embeddings", "registry.json")
BASE_INDEX_PATH = os.path.join(_BASE_DIR, "embeddings", "faiss_index")


def _index_key_from_json(json_path: str) -> str:
    """
    Derive index folder name from JSON filename.
    
    Example:
        data/structured.json → structured
        data/bharat_coking_coal_limited.json → bharat_coking_coal_limited
    """
    return os.path.splitext(os.path.basename(json_path))[0].lower()


def _hash_file(path: str) -> str:
    """
    Compute SHA-256 hash of file content.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_registry() -> dict:
    """Load the registry JSON file."""
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_registry(registry: dict) -> None:
    """Save the registry JSON file."""
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def get_index_path(json_path: str) -> str:
    """
    Get the index directory path for a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        Path to the FAISS index directory
    """
    index_key = _index_key_from_json(json_path)
    return os.path.join(BASE_INDEX_PATH, index_key)


def check_or_register_json(json_path: str) -> Tuple[str, str]:
    """
    Check if embeddings exist for this JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        Tuple of (action, index_path) where action is:
            - "load": Index exists and hash matches, can reuse
            - "rebuild": Index exists but hash differs, needs rebuild
            - "create": No index exists, needs creation
    """
    registry = _load_registry()
    
    index_key = _index_key_from_json(json_path)
    index_path = get_index_path(json_path)
    doc_hash = _hash_file(json_path)
    
    if index_key in registry:
        stored_hash = registry[index_key].get("doc_hash", "")
        
        # Check if index files actually exist
        index_file = os.path.join(index_path, "index.faiss")
        docs_file = os.path.join(index_path, "documents.json")
        
        if os.path.exists(index_file) and os.path.exists(docs_file):
            if stored_hash == doc_hash:
                return "load", index_path
            else:
                return "rebuild", index_path
    
    return "create", index_path


def update_registry(json_path: str) -> None:
    """
    Update registry after building an index.
    
    Args:
        json_path: Path to the JSON file that was indexed
    """
    registry = _load_registry()
    
    index_key = _index_key_from_json(json_path)
    
    registry[index_key] = {
        "json_file": os.path.basename(json_path),
        "doc_hash": _hash_file(json_path),
        "index_path": get_index_path(json_path),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    _save_registry(registry)
    print(f"📝 Registry updated for: {index_key}")


def remove_from_registry(json_path: str) -> bool:
    """
    Remove an entry from the registry.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        True if removed, False if not found
    """
    registry = _load_registry()
    index_key = _index_key_from_json(json_path)
    
    if index_key in registry:
        del registry[index_key]
        _save_registry(registry)
        return True
    
    return False


def list_registered_indexes() -> list:
    """
    List all registered indexes.
    
    Returns:
        List of dicts with index information
    """
    registry = _load_registry()
    return [
        {
            "key": key,
            **info
        }
        for key, info in registry.items()
    ]


# Legacy compatibility - maps old function signature to new one
def check_or_register_company(company_name: str, json_path: str) -> Tuple[str, str]:
    """
    DEPRECATED: Use check_or_register_json instead.
    Kept for backward compatibility.
    """
    return check_or_register_json(json_path)
