import json
import math

# Aggressive limit to prevent API timeouts on free tier
# Smaller chunks = faster responses
MAX_INPUT_TOKENS = 3000


def estimate_tokens(text: str) -> int:
    """
    Conservative token estimation for text.
    Uses word count * 1.3 as approximation.
    """
    if not text:
        return 0
    return int(len(str(text).split()) * 1.3)


def estimate_json_tokens(data) -> int:
    """
    Estimate tokens in a JSON-serializable data structure.
    Handles nested dicts, lists, and primitive types.
    """
    if data is None:
        return 1
    
    if isinstance(data, (str, int, float, bool)):
        return estimate_tokens(str(data))
    
    if isinstance(data, dict):
        total = 2  # {} brackets
        for key, value in data.items():
            total += estimate_tokens(str(key))  # key
            total += estimate_json_tokens(value)  # value
            total += 2  # colon and comma
        return total
    
    if isinstance(data, list):
        total = 2  # [] brackets
        for item in data:
            total += estimate_json_tokens(item)
            total += 1  # comma
        return total
    
    # Fallback for unknown types
    return estimate_tokens(json.dumps(data, ensure_ascii=False))


def split_text_by_tokens(text: str, max_tokens: int = MAX_INPUT_TOKENS):
    """
    Split text into token-safe chunks.
    """
    words = text.split()
    chunks = []
    current = []
    current_tokens = 0

    for word in words:
        word_tokens = estimate_tokens(word)
        
        if current_tokens + word_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            current = []
            current_tokens = 0
        
        current.append(word)
        current_tokens += word_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_list_by_tokens(items: list, max_tokens: int = MAX_INPUT_TOKENS):
    """
    Split a list into chunks where each chunk stays under max_tokens.
    Preserves individual items (doesn't split them).
    """
    if not items:
        return []
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for item in items:
        item_tokens = estimate_json_tokens(item)
        
        # If single item exceeds limit, include it anyway (will be handled by hierarchical chunking)
        if item_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            chunks.append([item])
            continue
        
        # If adding this item would exceed limit, start new chunk
        if current_tokens + item_tokens > max_tokens and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_tokens = 0
        
        current_chunk.append(item)
        current_tokens += item_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def chunk_data_by_tokens(data, max_tokens: int = MAX_INPUT_TOKENS):
    """
    Intelligently chunk any data structure to stay under token limit.
    Returns list of chunks.
    """
    total_tokens = estimate_json_tokens(data)
    
    # If under limit, return as-is
    if total_tokens <= max_tokens:
        return [data]
    
    # Handle different data types
    if isinstance(data, list):
        return chunk_list_by_tokens(data, max_tokens)
    
    if isinstance(data, dict):
        # For dicts, try to split by top-level keys
        chunks = []
        current_chunk = {}
        current_tokens = 0
        
        for key, value in data.items():
            item_tokens = estimate_json_tokens({key: value})
            
            if current_tokens + item_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = {}
                current_tokens = 0
            
            current_chunk[key] = value
            current_tokens += item_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [data]
    
    # For primitives or strings, split as text
    if isinstance(data, str):
        text_chunks = split_text_by_tokens(data, max_tokens)
        return text_chunks
    
    # Fallback: return as-is
    return [data]


def prepare_safe_data(data, max_tokens=MAX_INPUT_TOKENS):
    """
    Prepare data for Groq API with token-aware chunking.
    Returns the data in a token-safe format.
    """
    chunks = chunk_data_by_tokens(data, max_tokens)
    # Return first chunk if data was split, otherwise return as-is
    return chunks[0] if len(chunks) > 0 else data
