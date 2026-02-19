"""
Analysis Prompts for Structured IPO Analysis.

Fixed prompts for generating structured IPO analysis sections.
Uses ONLY prospectus data, no speculation or advice.
"""

# Analysis section prompts
ANALYSIS_SECTIONS = {
    "ipo_overview": {
        "title": "IPO Overview",
        "prompt": """Extract the IPO overview from the provided context:

REQUIRED INFORMATION:
- Company name and legal entity
- Sector / Industry (Explicitly state the sector, e.g., Technology, Healthcare, Finance)
- Issue size (fresh issue amount + OFS amount if any)
- Price band (face value and issue price range)
- Lot size and minimum investment
- Issue type (book building / fixed price)

RULES:
- Use ONLY information from the context
- If any field is missing, write "Not disclosed in prospectus"
- Do NOT calculate or infer values
- Present in a clear, structured format
- For "Sector / Industry", look for words like "Industry", "Sector", "Business Model", "Segment".

CONTEXT:
{context}

Provide the IPO Overview:"""
    },
    
    "key_strengths": {
        "title": "Key Strengths",
        "prompt": """List the key competitive strengths from the provided context.

RULES:
- Extract ONLY explicitly stated strengths from the prospectus
- Do NOT add your own opinions or analysis
- Do NOT speculate on future potential
- Maximum 7 key strengths
- Keep each point concise (1-2 sentences)

CONTEXT:
{context}

List the Key Strengths:"""
    },
    
    "key_weaknesses": {
        "title": "Key Weaknesses & Concerns",
        "prompt": """List the key business challenges or weaknesses from the provided context.

RULES:
- Extract ONLY information explicitly stated in the prospectus
- Include concerns mentioned in risk factors
- Do NOT add speculation
- Do NOT predict future problems
- Maximum 7 key concerns
- Keep each point concise

CONTEXT:
{context}

List the Key Weaknesses:"""
    },
    
    "business_risks": {
        "title": "Business Risks",
        "prompt": """Summarize the main risk factors disclosed in the prospectus.

RULES:
- Extract ONLY risks explicitly mentioned in the prospectus
- Categorize if possible (market risk, regulatory risk, operational risk, etc.)
- Do NOT speculate on undisclosed risks
- Do NOT provide severity ratings unless stated
- Maximum 10 risk factors

CONTEXT:
{context}

List the Business Risks:"""
    },
    
    "important_dates": {
        "title": "Important Dates",
        "prompt": """Extract all important IPO dates from the provided context.

REQUIRED DATES (if disclosed):
- Issue open date
- Issue close date
- Basis of allotment date
- Initiation of refunds
- Credit of shares to demat
- Listing date

RULES:
- Use ONLY dates from the prospectus
- If a date is not mentioned, write "Not disclosed"
- Present in chronological order

CONTEXT:
{context}

List the Important Dates:"""
    },
    
    "financial_highlights": {
        "title": "Financial Highlights",
        "prompt": """Extract key financial metrics from the provided context.

REQUIRED METRICS (if available):
- Revenue / Total Income (last 3 years/periods)
- Profit After Tax / Net Profit (last 3 years/periods)
- EBITDA and EBITDA margin
- Total Assets and Net Worth
- Debt to Equity ratio
- ROE / ROCE

RULES:
- Use ONLY numbers explicitly stated in the prospectus
- Include the period/financial year for each metric
- Do NOT calculate ratios unless explicitly given
- Do NOT make projections
- Present in a clear tabular format if possible

CONTEXT:
{context}

List the Financial Highlights:"""
    }
}


# Queries for retrieving relevant context for each section
SECTION_QUERIES = {
    "ipo_overview": [
        "issue size fresh issue offer for sale",
        "price band lot size book building",
        "IPO details issue structure",
        "face value equity shares"
    ],
    "key_strengths": [
        "competitive strengths advantages",
        "our strengths key advantages",
        "market leadership position",
        "competitive advantages strengths"
    ],
    "key_weaknesses": [
        "risk factors concerns",
        "challenges weaknesses",
        "business risks concerns",
        "internal risks factors affecting"
    ],
    "business_risks": [
        "risk factors",
        "risks relating to business",
        "risks relating to industry",
        "external risks regulatory risks"
    ],
    "important_dates": [
        "issue schedule timeline",
        "bid issue opening closing",
        "allotment listing date",
        "IPO dates schedule"
    ],
    "financial_highlights": [
        "financial information restated",
        "revenue profit EBITDA",
        "assets liabilities net worth",
        "financial summary key ratios"
    ]
}


def get_section_prompt(section_key: str, context: str) -> str:
    """
    Get the formatted prompt for a section with context.
    
    Args:
        section_key: Key from ANALYSIS_SECTIONS
        context: Retrieved context to include
        
    Returns:
        Formatted prompt string
    """
    if section_key not in ANALYSIS_SECTIONS:
        raise ValueError(f"Unknown section: {section_key}")
    
    section = ANALYSIS_SECTIONS[section_key]
    return section["prompt"].format(context=context)


def get_section_title(section_key: str) -> str:
    """Get the display title for a section."""
    return ANALYSIS_SECTIONS.get(section_key, {}).get("title", section_key)


def get_section_queries(section_key: str) -> list:
    """Get the retrieval queries for a section."""
    return SECTION_QUERIES.get(section_key, [])
