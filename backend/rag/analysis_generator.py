"""
Analysis Generator for Structured IPO Analysis.

Generates structured analysis sections before enabling free chat.
Uses RAG retrieval + LLM with strict non-hallucination prompts.
"""

import os
import json
from typing import Dict, Any, List

from retriever import retrieve
from llm_cerebras import generate_answer
from analysis_prompts import (
    ANALYSIS_SECTIONS,
    get_section_prompt,
    get_section_title,
    get_section_queries
)

# System prompt for analysis generation
ANALYSIS_SYSTEM_PROMPT = """You are an IPO analysis assistant that extracts information from prospectus documents.

STRICT RULES:
1. Use ONLY the provided context to generate your analysis.
2. If information is NOT in the context, clearly state "Not disclosed in the prospectus."
3. Do NOT make up numbers, dates, or facts.
4. Do NOT provide investment advice or recommendations.
5. Do NOT predict stock prices or market performance.
6. Present information in a clear, structured format.
7. Be factual and neutral in tone.
"""


def _retrieve_for_section(json_path: str, section_key: str, top_k: int = 10) -> List[Dict]:
    """
    Retrieve relevant documents for a section.
    
    Uses multiple queries to get comprehensive context.
    """
    queries = get_section_queries(section_key)
    
    all_results = []
    seen_texts = set()
    
    for query in queries:
        results = retrieve(json_path, query, top_k=top_k // len(queries) + 1)
        for r in results:
            text = r.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_results.append(r)
    
    return all_results[:top_k]


def _build_context(documents: List[Dict], max_chars: int = 8000) -> str:
    """
    Build context string from retrieved documents.
    
    Limits total characters for token safety.
    """
    context_parts = []
    total_chars = 0
    
    for doc in documents:
        text = doc.get("text", "").strip()
        meta = doc.get("metadata", {})
        
        if not text:
            continue
        
        # Format with source info
        section = meta.get("section", "Unknown")
        page = meta.get("page", -1)
        
        if page >= 0:
            formatted = f"[Section: {section}, Page: {page}]\n{text}"
        else:
            formatted = f"[Section: {section}]\n{text}"
        
        # Check character limit
        if total_chars + len(formatted) > max_chars:
            break
        
        context_parts.append(formatted)
        total_chars += len(formatted)
    
    return "\n\n---\n\n".join(context_parts)


def generate_section_analysis(json_path: str, section_key: str) -> Dict[str, Any]:
    """
    Generate analysis for a single section.
    
    Args:
        json_path: Path to the indexed JSON file
        section_key: Key from ANALYSIS_SECTIONS
        
    Returns:
        dict with 'title', 'content', 'sources', 'success'
    """
    try:
        # Retrieve relevant documents
        documents = _retrieve_for_section(json_path, section_key)
        
        if not documents:
            return {
                "title": get_section_title(section_key),
                "content": "No relevant information found in the prospectus for this section.",
                "sources": [],
                "success": False
            }
        
        # Build context
        context = _build_context(documents)
        
        # Get prompt
        user_prompt = get_section_prompt(section_key, context)
        
        # Generate with LLM
        response = generate_answer(ANALYSIS_SYSTEM_PROMPT, user_prompt)
        
        # Extract sources
        sources = []
        for doc in documents:
            meta = doc.get("metadata", {})
            page = meta.get("page", -1)
            if page >= 0 and page not in sources:
                sources.append(page)
        
        return {
            "title": get_section_title(section_key),
            "content": response.strip(),
            "sources": sorted(sources)[:5],  # Top 5 source pages
            "success": True
        }
        
    except Exception as e:
        return {
            "title": get_section_title(section_key),
            "content": f"Error generating analysis: {str(e)}",
            "sources": [],
            "success": False
        }


def generate_structured_analysis(json_path: str) -> Dict[str, Any]:
    """
    Generate all structured analysis sections.
    
    Args:
        json_path: Path to the indexed JSON file
        
    Returns:
        dict with all 6 analysis sections
    """
    print(f"📊 Generating structured analysis for: {os.path.basename(json_path)}")
    
    analysis = {
        "json_file": os.path.basename(json_path),
        "sections": {},
        "success_count": 0,
        "total_count": len(ANALYSIS_SECTIONS)
    }
    
    for section_key in ANALYSIS_SECTIONS:
        print(f"   📝 {get_section_title(section_key)}...")
        
        section_result = generate_section_analysis(json_path, section_key)
        analysis["sections"][section_key] = section_result
        
        if section_result["success"]:
            analysis["success_count"] += 1
            print(f"      ✅ Done")
        else:
            print(f"      ⚠️ Limited data")
    
    print(f"✅ Analysis complete: {analysis['success_count']}/{analysis['total_count']} sections")
    
    return analysis


def save_analysis(analysis: Dict, output_path: str) -> str:
    """
    Save analysis to a JSON file.
    
    Args:
        analysis: Analysis dict from generate_structured_analysis
        output_path: Path to save the JSON
        
    Returns:
        Path to the saved file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved analysis: {output_path}")
    return output_path


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Default test file
    test_json = os.path.join(os.path.dirname(__file__), "data", "structured.json")
    
    if len(sys.argv) > 1:
        test_json = sys.argv[1]
    
    if os.path.exists(test_json):
        print(f"Generating analysis for: {test_json}")
        analysis = generate_structured_analysis(test_json)
        
        # Print results
        print("\n" + "=" * 60)
        for key, section in analysis["sections"].items():
            print(f"\n### {section['title']}\n")
            print(section["content"][:500] + "..." if len(section["content"]) > 500 else section["content"])
            print()
    else:
        print(f"File not found: {test_json}")
