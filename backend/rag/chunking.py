import json
from typing import List, Dict, Any

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def chunk_text(text: str) -> List[str]:
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def normalize_json(data: Any) -> List[Dict]:
    normalized = []

    # Case 1: list of dicts
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                normalized.append({
                    "section": str(item.get("section", "Unknown")),
                    "page": item.get("page", -1),
                    "content": str(item.get("content", ""))
                })
            elif isinstance(item, str):
                normalized.append({
                    "section": "Unknown",
                    "page": -1,
                    "content": item
                })
        return normalized

    # Case 2: dict
    if isinstance(data, dict):
        for k, v in data.items():
            normalized.append({
                "section": str(k),
                "page": -1,
                "content": str(v)
            })
        return normalized

    # Case 3: raw string
    if isinstance(data, str):
        return [{
            "section": "Unknown",
            "page": -1,
            "content": data
        }]

    raise ValueError("Unsupported JSON format for RAG")


def load_and_chunk(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    data = normalize_json(raw_data)
    documents = []

    for item in data:
        section = item["section"]
        page = item["page"]
        content = item["content"]

        # SAFETY: ensure string
        if not isinstance(content, str):
            content = str(content)

        content = content.strip()
        if len(content) < 50:
            continue

        chunks = chunk_text(content)

        for idx, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "metadata": {
                    "section": section,
                    "page": page,
                    "chunk_id": idx
                }
            })

    return documents
