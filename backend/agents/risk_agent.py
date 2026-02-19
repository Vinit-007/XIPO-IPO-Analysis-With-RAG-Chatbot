"""
Risk Agent - Rule-Based Risk Extraction

SCOPE:
- Extracts explicitly stated risks from RHP text
- NO inference, NO scoring, NO LLM
- Deterministic, safe extraction
"""

import re


RISK_KEYWORDS = [
    "risk",
    "litigation",
    "regulatory",
    "penalty",
    "compliance",
    "dependency",
    "volatility",
    "uncertainty",
    "competition",
    "government policy",
    "environment",
    "legal proceedings"
]


def extract_risks(structured_json: dict) -> dict:
    """
    Extract explicit risk-related statements from document text.

    Args:
        structured_json: Output of Stage 3 extractor

    Returns:
        {
            "risks": [
                {
                    "page": 12,
                    "text": "Our business is subject to regulatory risk..."
                }
            ],
            "confidence": "high (rule-based, no inference)"
        }
    """

    risks = []

    for page in structured_json.get("pages", []):
        page_number = page.get("page_number")
        text = page.get("text", "")

        text_lower = text.lower()

        for keyword in RISK_KEYWORDS:
            if keyword in text_lower:
                risks.append({
                    "page": page_number,
                    "text": text.strip()
                })
                break  # avoid duplicate risk entries per page

    return {
        "risks": risks,
        "risk_count": len(risks),
        "confidence": "high (rule-based, no inference)"
    }
