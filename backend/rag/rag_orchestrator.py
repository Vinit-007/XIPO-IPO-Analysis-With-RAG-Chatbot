"""
RAG Orchestrator - Unified entry point for the RAG pipeline.

This module coordinates:
1. PDF → JSON extraction
2. JSON → FAISS index (with hash-based caching)
3. Retrieval + Chat interface

Uses JSON filename as the single source of truth for downstream operations.
"""

import os
import json
import shutil
from typing import Optional, Dict, Any

# Import existing components
from index_manager import check_or_register_json, update_registry, get_index_path
from embed_store import build_index
from retriever import retrieve
from analysis_generator import generate_structured_analysis
from rag_chatbot_v2 import chat, is_question_blocked, get_blocked_response

# Constants
RAG_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAG_EMBEDDINGS_DIR = os.path.join(os.path.dirname(__file__), "embeddings")


def derive_json_name(company_name: str) -> str:
    """
    Derive a safe JSON filename from company name.
    
    Example:
        "Bharat Coking Coal Limited" → "bharat_coking_coal_limited"
    """
    return company_name.lower().replace(" ", "_").replace("-", "_")


def get_json_path(company_name: str) -> str:
    """
    Get the expected JSON path for a company.
    
    Args:
        company_name: Company name string
        
    Returns:
        Absolute path to backend/rag/data/<derived_name>.json
    """
    name = derive_json_name(company_name)
    return os.path.join(RAG_DATA_DIR, f"{name}.json")


def copy_extracted_json(source_json_path: str, company_name: str) -> str:
    """
    Copy extracted JSON to RAG data directory.
    
    Args:
        source_json_path: Path to the extracted structured.json
        company_name: Company name for deriving target filename
        
    Returns:
        Path to the copied JSON in RAG data directory
    """
    os.makedirs(RAG_DATA_DIR, exist_ok=True)
    
    target_path = get_json_path(company_name)
    
    if source_json_path != target_path:
        shutil.copy2(source_json_path, target_path)
        print(f"📋 Copied JSON to RAG data: {os.path.basename(target_path)}")
    
    return target_path


def get_index_status(json_path: str) -> Dict[str, Any]:
    """
    Check if embeddings exist for a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        dict with keys:
            - exists: bool - whether index exists
            - hash_match: bool - whether hash matches (no changes)
            - index_path: str - path to index directory
            - action: str - "load", "rebuild", or "create"
    """
    if not os.path.exists(json_path):
        return {
            "exists": False,
            "hash_match": False,
            "index_path": None,
            "action": "error",
            "error": f"JSON file not found: {json_path}"
        }
    
    action, index_path = check_or_register_json(json_path)
    
    return {
        "exists": action == "load",
        "hash_match": action == "load",
        "index_path": index_path,
        "action": action
    }


def ensure_indexed(json_path: str) -> str:
    """
    Ensure JSON file is indexed in FAISS.
    
    - If embeddings exist and hash matches → skip (reuse)
    - If embeddings exist but hash differs → rebuild
    - If no embeddings → create new
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        Path to the FAISS index directory
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    status = get_index_status(json_path)
    
    if status["action"] == "load":
        print(f"✅ Index already exists for {os.path.basename(json_path)}, skipping embedding.")
        return status["index_path"]
    
    # Build index (handles "create" and "rebuild" cases)
    print(f"🔨 Building index for {os.path.basename(json_path)}...")
    build_index(json_path)
    
    return get_index_path(json_path)


def process_company_for_rag(
    company_name: str,
    source_json_path: str,
    generate_analysis: bool = True
) -> Dict[str, Any]:
    """
    Main orchestrator function for processing a company through RAG pipeline.
    
    Steps:
    1. Copy JSON to RAG data directory
    2. Build/load FAISS embeddings
    3. Optionally generate structured analysis
    
    Args:
        company_name: Company name
        source_json_path: Path to extracted structured.json
        generate_analysis: Whether to generate structured analysis
        
    Returns:
        dict with:
            - json_path: Path to JSON in RAG data dir
            - index_path: Path to FAISS index
            - analysis: Structured analysis (if requested)
            - ready: bool - whether RAG is ready for chat
    """
    result = {
        "company_name": company_name,
        "json_path": None,
        "index_path": None,
        "analysis": None,
        "ready": False,
        "error": None
    }
    
    try:
        # Step 1: Copy JSON to RAG data directory
        json_path = copy_extracted_json(source_json_path, company_name)
        result["json_path"] = json_path
        
        # Step 2: Ensure indexed
        index_path = ensure_indexed(json_path)
        result["index_path"] = index_path
        
        # Step 3: Generate structured analysis
        if generate_analysis:
            print("📊 Generating structured analysis...")
            analysis = generate_structured_analysis(json_path)
            result["analysis"] = analysis
        
        result["ready"] = True
        print(f"✅ RAG ready for {company_name}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ RAG processing failed: {e}")
    
    return result


def rag_chat(json_path: str, question: str) -> Dict[str, Any]:
    """
    Chat interface for RAG queries.
    
    Args:
        json_path: Path to the indexed JSON file
        question: User's question
        
    Returns:
        dict with 'answer', 'sources', and 'blocked' keys
    """
    # Check for blocked questions first
    if is_question_blocked(question):
        return {
            "answer": get_blocked_response(),
            "sources": [],
            "blocked": True
        }
    
    # Use the chatbot
    response = chat(json_path, question)
    response["blocked"] = False
    
    return response


def rag_retrieve(json_path: str, query: str, top_k: int = 5) -> list:
    """
    Retrieve relevant chunks for a query.
    
    Args:
        json_path: Path to the indexed JSON file
        query: Search query
        top_k: Number of results to return
        
    Returns:
        List of document chunks with text and metadata
    """
    return retrieve(json_path, query, top_k)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("RAG Orchestrator - Test Mode")
    print("=" * 60)
    
    # Test with existing structured.json
    test_json = os.path.join(RAG_DATA_DIR, "structured.json")
    
    if os.path.exists(test_json):
        print(f"\nTesting with: {test_json}")
        
        # Check status
        status = get_index_status(test_json)
        print(f"Index status: {status}")
        
        # Ensure indexed
        index_path = ensure_indexed(test_json)
        print(f"Index path: {index_path}")
        
        # Test retrieval
        print("\nTesting retrieval...")
        results = rag_retrieve(test_json, "What is the company's business?", top_k=3)
        print(f"Found {len(results)} results")
        
    else:
        print(f"No test file at: {test_json}")
        print("Run extraction first to create structured.json")
