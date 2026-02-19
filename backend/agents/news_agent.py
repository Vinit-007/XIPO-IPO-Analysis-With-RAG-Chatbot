"""
Semantic News Analysis Agent.

This module provides advanced news analysis using:
1. LLM-based semantic understanding (Impact on specific IPO/Sector)
2. Time-decay weighting (Newer news matters more)
3. Narrative generation (Explains WHY it matters)
"""

import os
import json
import logging
import requests
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cerebras Configuration (Reuse from groq_map_agent.py/rag_chatbot.py)
CEREBRAS_API_KEY = "csk-e8der3hkvt6hn2w6efr48d6wx6w9d98tey4t49n5jvvx3wtp"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "llama-3.3-70b"


def calculate_weighted_score(base_sentiment: int, days_old: int) -> float:
    """
    Apply time decay to sentiment score.
    
    Formula: Score * max(0, 1 - (days_old / 20))
    This ensures news older than 20 days has 0 impact.
    """
    if days_old > 20:
        return 0.0
    
    # Linear decay
    weight = max(0.0, 1.0 - (days_old / 20.0))
    weighted_score = base_sentiment * weight
    
    return round(weighted_score, 2)


def analyze_news_impact(company_name: str, sector: str, news_items: list) -> dict:
    """
    Analyze the impact of news on the company's IPO using LLM.
    
    Args:
        company_name: Name of the IPO company
        sector: Sector the company belongs to
        news_items: List of news dicts (headline, summary, days_old)
        
    Returns:
        dict with:
            - narrative: Analyst summary
            - sentiment_score: -10 to +10 score
            - sentiment_label: Positive/Negative/Neutral
            - key_factors: List of key influencing news
    """
    if not news_items:
        return {
            "narrative": "No recent news found for this company or sector.",
            "sentiment_score": 0,
            "sentiment_label": "NEUTRAL",
            "key_factors": []
        }

    # Prepare context for LLM
    news_text = ""
    for idx, item in enumerate(news_items[:15]): # Limit to top 15
        news_text += f"{idx+1}. [{item.get('days_old', 0)} days ago] {item['headline']}\n"

    prompt = f"""
You are a Senior IPO Analyst. Analyze the following recent news for "{company_name}" (Sector: {sector}).

Goal: Determine how this news impacts the upcoming IPO sentiment.

RULES:
1. Focus on recent news. Older news matters less.
2. Context Matters: "Battery prices dropping" is POSITIVE for an EV maker like Ola, but NEGATIVE for a battery maker.
3. Sector Trends: If the sector is booming (e.g., "Bull run in IT"), applying companies benefit.
4. Output a JSON object ONLY.

NEWS DATA:
{news_text}

OUTPUT JSON FORMAT:
{{
    "narrative": "A concise 3-4 sentence financial analyst summary explaining the sentiment. Mention specific drivers.",
    "sentiment_score": <Integer between -10 (Very Negative) and +10 (Very Positive)>,
    "key_factors": ["List of 2-3 short bullet points summarizing key drivers"]
}}
"""

    try:
        response = requests.post(
            CEREBRAS_URL,
            headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "You are a financial analyst JSON generator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        analysis = json.loads(content)
        
        # Post-process score with time decay heuristic aggregation
        # (The LLM gives an overall qualitative score, but we double check with hard logic if needed)
        # For now, trust the LLM's synthesis but ensure bounds
        score = max(-10, min(10, analysis.get("sentiment_score", 0)))
        
        label = "NEUTRAL"
        if score >= 3: label = "POSITIVE"
        if score >= 7: label = "VERY POSITIVE"
        if score <= -3: label = "NEGATIVE"
        if score <= -7: label = "VERY NEGATIVE"

        return {
            "narrative": analysis.get("narrative", "Analysis failed."),
            "sentiment_score": score,
            "sentiment_label": label,
            "key_factors": analysis.get("key_factors", [])
        }

    except Exception as e:
        logger.error(f"News Analysis Agent Failed: {e}")
        return {
            "narrative": "Unable to generate semantic analysis due to technical error.",
            "sentiment_score": 0,
            "sentiment_label": "NEUTRAL",
            "key_factors": []
        }

if __name__ == "__main__":
    # Test Run
    test_news = [
        {"headline": "EV sales drop by 10% in January", "days_old": 2},
        {"headline": "Government announces new subsidy for electric scooters", "days_old": 5},
        {"headline": "Ola Electric plans largest IPO in sector", "days_old": 15}
    ]
    print(analyze_news_impact("Ola Electric", "Automobile/EV", test_news))
