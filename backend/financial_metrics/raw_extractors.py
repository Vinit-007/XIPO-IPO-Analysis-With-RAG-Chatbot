"""
Extractors for financial_metrics.json structure
This works with the actual data format from the IPO analysis pipeline
"""
import re


def _clean_year(year_str: str) -> str:
    """Clean and normalize year strings"""
    if not year_str:
        return ""
    # Remove newlines and extra spaces
    clean = year_str.replace("\n", " ").strip()
    # Extract fiscal year if present
    match = re.search(r'(?:March 31,?\s*)?(\d{4})', clean)
    if match:
        return f"FY{match.group(1)}"
    match = re.search(r'September 30,?\s*(\d{4})', clean)
    if match:
        return f"H1{match.group(1)}"
    return clean[:20]  # Truncate long strings


def _parse_value(val_str: str) -> float | None:
    """Parse value strings with parentheses for negative numbers"""
    if not val_str:
        return None
    try:
        s = str(val_str).strip()
        is_neg = False
        if "(" in s and ")" in s:
            is_neg = True
            s = s.replace("(", "").replace(")", "")
        s = s.replace(",", "").replace("%", "").replace("₹", "")
        if s.lower() in ['negligible', 'nil', '-', '']:
            return 0.0
        val = float(s)
        return -val if is_neg else val
    except:
        return None


def _extract_metric_by_keywords(data: dict, keywords: list) -> dict:
    """
    Extract metrics matching keywords from financial_summary structure
    Returns dict: {clean_year: float_value}
    """
    financial_summary = data.get("financial_summary", {})
    result = {}
    
    for metric_name, metric_block in financial_summary.items():
        name_lower = metric_name.lower()
        if any(kw in name_lower for kw in keywords):
            for v in metric_block.get("values", []):
                year = _clean_year(v.get("year", ""))
                val = _parse_value(v.get("value"))
                if year and val is not None:
                    result[year] = val
    
    return result


def extract_revenue(data: dict) -> dict:
    """Extract revenue from operations by year"""
    return _extract_metric_by_keywords(data, ["revenue from", "revenue from operations"])


def extract_ebitda(data: dict) -> dict:
    """Extract EBITDA by year"""
    return _extract_metric_by_keywords(data, ["ebitda", "adjusted ebitda"])


def extract_pat(data: dict) -> dict:
    """Extract Profit After Tax (or loss) by year"""
    return _extract_metric_by_keywords(data, ["restated loss", "profit for", "loss for"])


def extract_eps(data: dict) -> dict:
    """Extract Earnings Per Share by year"""
    return _extract_metric_by_keywords(data, ["earnings per share", "loss per share", "eps"])


def extract_total_income(data: dict) -> dict:
    """Extract total income by year"""
    return _extract_metric_by_keywords(data, ["total income"])
