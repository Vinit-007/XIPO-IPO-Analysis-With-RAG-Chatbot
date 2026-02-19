"""
RAG Chatbot V2 - Non-Hallucinating IPO Chat Assistant.

This is the unified chatbot that uses:
- File-based RAG retrieval (json_path as source)
- Strict non-hallucination rules
- Cerebras LLM for answer generation

Replaces the old rag_chat.py with improved architecture.
"""

import os
from typing import Dict, Any, List

from retriever import retrieve
from llm_cerebras import generate_answer
from prompts import SYSTEM_PROMPT, USER_PROMPT

# Blocked question patterns (investment advice)
BLOCKED_PATTERNS = [
    "should i invest",
    "should i buy",
    "should i sell",
    "will stock go up",
    "will share go up",
    "will price increase",
    "will price decrease",
    "target price",
    "price target",
    "good buy",
    "bad buy",
    "is it worth",
    "will it rise",
    "will it fall",
    "prediction",
    "forecast price",
    "recommend buying",
    "recommend selling",
    "should i apply",
    "listing gains",
    "grey market premium",
    "gmp"
]


def is_question_blocked(question: str) -> bool:
    """
    Check if the question is asking for investment advice.
    
    Args:
        question: User's question string
        
    Returns:
        True if question should be blocked
    """
    q_lower = question.lower()
    return any(pattern in q_lower for pattern in BLOCKED_PATTERNS)


def get_blocked_response() -> str:
    """Return a polite refusal for blocked questions."""
    return """I cannot provide investment advice, price predictions, or buy/sell recommendations.

As an IPO analysis assistant, I can only provide factual information from the prospectus, such as:

• Company financials and business overview
• Risk factors disclosed in the RHP
• IPO structure (fresh issue vs OFS)
• Promoter and shareholding details
• Important dates and timelines

Please ask me about any of these topics instead!"""


def get_not_available_response() -> str:
    """Standard response when data is not in prospectus."""
    return "This information is not available in the prospectus. Please try asking about other aspects of the IPO that are covered in the RHP document."


def _build_context(documents: List[Dict], max_chars: int = 6000) -> str:
    """
    Build context string from retrieved documents.
    
    Args:
        documents: List of retrieved document chunks
        max_chars: Maximum characters for token safety
        
    Returns:
        Formatted context string
    """
    if not documents:
        return ""
    
    context_parts = []
    total_chars = 0
    
    for doc in documents:
        text = doc.get("text", "").strip()
        meta = doc.get("metadata", {})
        
        if not text:
            continue
        
        page = meta.get("page", -1)
        section = meta.get("section", "")
        
        # Format with source info
        if page >= 0:
            formatted = f"[Page {page}] {text}"
        elif section:
            formatted = f"[{section}] {text}"
        else:
            formatted = text
        
        # Check character limit
        if total_chars + len(formatted) > max_chars:
            # Add truncated version
            remaining = max_chars - total_chars
            if remaining > 100:
                context_parts.append(formatted[:remaining] + "...")
            break
        
        context_parts.append(formatted)
        total_chars += len(formatted)
    
    return "\n\n".join(context_parts)


def chat(json_path: str, question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Main chat interface for RAG queries.
    
    Args:
        json_path: Path to the indexed JSON file
        question: User's question
        top_k: Number of chunks to retrieve
        
    Returns:
        dict with 'answer', 'sources', 'retrieved_count'
    """
    # Check for blocked questions
    if is_question_blocked(question):
        return {
            "answer": get_blocked_response(),
            "sources": [],
            "retrieved_count": 0,
            "blocked": True
        }
    
    # Retrieve relevant documents
    try:
        documents = retrieve(json_path, question, top_k=top_k)
    except FileNotFoundError as e:
        return {
            "answer": f"Error: Index not found. Please ensure the document has been processed. ({e})",
            "sources": [],
            "retrieved_count": 0,
            "blocked": False
        }
    except Exception as e:
        return {
            "answer": f"Error retrieving context: {str(e)}",
            "sources": [],
            "retrieved_count": 0,
            "blocked": False
        }
    
    # Check if we got any results
    if not documents:
        return {
            "answer": get_not_available_response(),
            "sources": [],
            "retrieved_count": 0,
            "blocked": False
        }
    
    # Build context
    context = _build_context(documents)
    
    if not context.strip():
        return {
            "answer": get_not_available_response(),
            "sources": [],
            "retrieved_count": 0,
            "blocked": False
        }
    
    # Format the prompt
    user_prompt = USER_PROMPT.format(
        context=context,
        question=question
    )
    
    # Generate answer
    try:
        answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "retrieved_count": len(documents),
            "blocked": False
        }
    
    # Extract source pages
    sources = []
    for doc in documents:
        meta = doc.get("metadata", {})
        page = meta.get("page", -1)
        if page >= 0 and page not in sources:
            sources.append(page)
    
    return {
        "answer": answer.strip(),
        "sources": sorted(sources),
        "retrieved_count": len(documents),
        "blocked": False
    }


def chat_with_context(question: str, contexts: List[Dict]) -> Dict[str, Any]:
    """
    Alternative chat interface using pre-built contexts.
    
    This is for compatibility with the old context_builder approach.
    
    Args:
        question: User's question
        contexts: Pre-built context list from context_builder
        
    Returns:
        dict with 'answer' and 'sources'
    """
    # Check for blocked questions
    if is_question_blocked(question):
        return {
            "answer": get_blocked_response(),
            "sources": [],
            "blocked": True
        }
    
    if not contexts:
        return {
            "answer": get_not_available_response(),
            "sources": [],
            "blocked": False
        }
    
    # Simple keyword-based retrieval for pre-built contexts
    from chatbot.retriever import retrieve_contexts
    
    relevant = retrieve_contexts(question, contexts, limit=6)
    
    if not relevant:
        return {
            "answer": get_not_available_response(),
            "sources": [],
            "blocked": False
        }
    
    # Build context text
    context_parts = []
    for ctx in relevant:
        ctx_type = ctx.get('type', 'unknown').upper()
        source = ctx.get('source', 'Unknown')
        text = ctx.get('text', '')[:2000]  # Truncate for safety
        context_parts.append(f"[{ctx_type} | {source}]\n{text}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Format prompt
    user_prompt = USER_PROMPT.format(
        context=context,
        question=question
    )
    
    # Generate answer
    try:
        answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "sources": [],
            "blocked": False
        }
    
    # Extract sources
    sources = list(set(ctx.get("source", "Unknown") for ctx in relevant))
    
    return {
        "answer": answer.strip(),
        "sources": sources,
        "blocked": False
    }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Default test file
    test_json = os.path.join(os.path.dirname(__file__), "data", "structured.json")
    
    if len(sys.argv) > 1:
        test_json = sys.argv[1]
    
    print("=" * 60)
    print("RAG Chatbot V2 - Test Mode")
    print("=" * 60)
    print(f"Using index from: {test_json}")
    print("Type 'exit' to quit\n")
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() == "exit":
            break
        
        if not question:
            continue
        
        print("\nThinking...")
        result = chat(test_json, question)
        
        print(f"\nAnswer:\n{result['answer']}")
        
        if result['sources']:
            print(f"\nSources: Pages {result['sources']}")
        
        if result.get('blocked'):
            print("(Question was blocked)")
