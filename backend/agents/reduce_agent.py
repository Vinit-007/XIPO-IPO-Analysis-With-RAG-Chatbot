import os
import requests

# Cerebras API config
CEREBRAS_API_KEY = "csk-e8der3hkvt6hn2w6efr48d6wx6w9d98tey4t49n5jvvx3wtp"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "llama-3.3-70b"


def run_reduce_stage(partials, output_path):
    print("🧠 REDUCE — Final IPO synthesis")

    prompt = """
You are an IPO research analyst at a top brokerage.

Your task:
Combine multiple partial IPO analysis sections into ONE final, decision-focused IPO report.

IMPORTANT RULES (STRICT):
1. Use ONLY the provided content — do NOT invent numbers, dates, or facts.
2. If something is not disclosed in the prospectus, explicitly say "Not disclosed".
3. NEVER use vague disclaimers like "investors should evaluate carefully".
4. Be decisive, analytical, and structured like a broker IPO note.
5. No marketing language. No hedging. No repetition.
6. Do NOT mention chunks, summaries, or sources.
7. Do NOT give a "SUBSCRIBE" or "AVOID" recommendation. Provide facts and analysis only.
8. Output MUST be clean Markdown.

TONE:
- Professional
- Confident
- Analytical
- Investor-facing

STRUCTURE (FOLLOW EXACTLY):

# <Company Name> — IPO Report
Decision-focused IPO analysis (auto-generated)

## IPO Overview
- **Company Name**
- **Company Sector**

## Key Strengths
List 3–5 bullet points.
Each bullet MUST follow this format:
**Fact → Why it matters → Impact on investors**

Example:
- Government-backed promoter → stable operations → lower execution risk

## Key Risks
List 3–5 bullet points.
Each bullet MUST follow this format:
**Risk → Why it matters → Potential downside**

## Issue Details
Present as a table.
Use "Not disclosed" where applicable.

## Important Dates
Present as a table.
If IPO already listed, mention listing date clearly.

## Financial Snapshot
Summarize revenue, profit trends, and volatility.
- Use exact numbers if provided
- Do NOT calculate ratios
- Do NOT infer margins

## Final Investment View
One concise paragraph summarizing:
- Risk–reward balance
- Suitable investor profile
- Key watch-outs post listing

END OUTPUT.

SECTIONS TO ASSEMBLE:
""" + "\n\n---\n\n".join(partials)

    print("   🌐 Calling Cerebras API for reduce...")
    response = requests.post(
        CEREBRAS_URL,
        headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4000
        },
        timeout=90
    )
    result = response.json()
    
    if "error" in result:
        print(f"   ❌ Reduce failed: {result['error']}")
        final_report = "\n\n".join(partials)  # Fallback: just join the sections
    else:
        final_report = result["choices"][0]["message"]["content"]
        print("   ✅ Reduce successful")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_report)

