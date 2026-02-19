try:
    from financial_metrics.unit_normalizer import to_crore
except ImportError:
    from unit_normalizer import to_crore
import re

def parse_year(year_str: str) -> str:
    """Extract fiscal year from year string like 'March 31, 2025' -> 'FY2025'"""
    if not year_str:
        return None
    # Match patterns like "March 31, 2025" or "year ended March 31, 2025"
    match = re.search(r'(?:March\s*31,?\s*)?(\d{4})', year_str)
    if match:
        return f"FY{match.group(1)}"
    # Handle "September 30, 2025" etc
    match = re.search(r'(?:September\s*30,?\s*)?(\d{4})', year_str)
    if match:
        return f"H1FY{match.group(1)}"
    return None

def parse_value(val_str: str) -> float:
    """Parse value string like '93,899.03' or '(39,417.05)' into float"""
    if not val_str or not isinstance(val_str, str):
        return None
    # Remove commas
    val_str = val_str.replace(',', '')
    # Handle negative values in parentheses like (123.45)
    if val_str.startswith('(') and val_str.endswith(')'):
        val_str = '-' + val_str[1:-1]
    try:
        return float(val_str)
    except ValueError:
        return None

def extract_metrics_from_summary(financial_summary: dict) -> dict:
    """Transform financial_summary structure into flat {metric: {year: value}} format"""
    result = {
        "revenue": {},
        "pat": {},  # Profit After Tax (or loss)
        "ebitda": {},
        "eps": {},
        "total_income": {},
        "total_assets": {},
        "net_worth": {},
        "total_debt": {}
    }
    
    for metric_name, metric_data in financial_summary.items():
        if not isinstance(metric_data, dict) or 'values' not in metric_data:
            continue
        
        # Identify metric type by name
        name_lower = metric_name.lower()
        target_key = None
        
        if 'revenue from' in name_lower and 'operations' in name_lower:
            target_key = "revenue"
        elif any(x in name_lower for x in ['profit', 'loss', 'pat']) and any(y in name_lower for y in ['for the period', 'for the year', 'after tax', 'restated profit']):
            target_key = "pat"
        elif 'ebitda' in name_lower and 'adjusted' not in name_lower:
            target_key = "ebitda"
        elif any(x in name_lower for x in ['basic', 'diluted', 'eps']) and any(y in name_lower for y in ['per share', 'earnings']):
            target_key = "eps"
        elif 'total income' in name_lower:
            target_key = "total_income"
        elif 'total assets' in name_lower or 'total equity and liabilities' in name_lower:
            target_key = "total_assets"
        elif 'net worth' in name_lower or 'total equity' in name_lower:
            target_key = "net_worth"
        elif 'total borrowings' in name_lower or 'total debt' in name_lower or name_lower == 'borrowings':
            target_key = "total_debt"
        
        if not target_key:
            continue
            
        for val_entry in metric_data.get('values', []):
            year = parse_year(val_entry.get('year', ''))
            value = parse_value(val_entry.get('value', ''))
            if year and value is not None:
                # Only overwrite if not already set (prefer first match)
                if year not in result[target_key]:
                    result[target_key][year] = value
    
    return result

def normalize_raw_metrics(raw_metrics: dict):
    """Normalize metrics from financial_summary format"""
    # First transform from nested structure to flat structure
    extracted = extract_metrics_from_summary(raw_metrics)
    
    normalized = {}
    for metric, values in extracted.items():
        normalized[metric] = {}
        for period, val in values.items():
            if metric in ["revenue", "pat", "ebitda", "total_income", "total_assets", "net_worth", "total_debt"]:
                normalized[metric][period] = to_crore(val)
            else:
                # EPS etc → leave untouched
                normalized[metric][period] = val
    
    return normalized


def compute_metrics(normalized):
    revenue = normalized.get("revenue", {})
    pat = normalized.get("pat", {})
    ebitda = normalized.get("ebitda", {})

    metrics = {}

    # Revenue growth - get FY keys sorted
    fy_years = sorted([k for k in revenue if k.startswith("FY")])
    growth = {}
    for i in range(1, len(fy_years)):
        prev, curr = fy_years[i-1], fy_years[i]
        if revenue.get(prev) and revenue.get(curr):
            growth[curr] = round(
                (revenue[curr] - revenue[prev]) / abs(revenue[prev]) * 100, 2
            )

    metrics["revenue_growth_pct"] = growth

    # Profit margin
    margins = {}
    for year in pat:
        if year in revenue and revenue[year]:
            margins[year] = round((pat[year] / revenue[year]) * 100, 2)

    metrics["profit_margin_pct"] = margins

    # EBITDA margin
    ebitda_margin = {}
    for year in ebitda:
        if year in revenue and revenue[year]:
            ebitda_margin[year] = round((ebitda[year] / revenue[year]) * 100, 2)

    metrics["ebitda_margin_pct"] = ebitda_margin

    return metrics
