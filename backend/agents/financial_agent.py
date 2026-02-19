"""
Financial Agent - Rule-Based Financial Metric Extraction

SCOPE:
- Extracts ONLY explicitly stated financial metrics from tables
- NO inference, estimation, or computation
- Preserves all values as strings
- Deterministic, rule-based logic only

LIMITATIONS:
- Does NOT compute margins or ratios
- Does NOT fill missing data
- Does NOT normalize values
- Does NOT use ML/LLM
"""

import re


# Target financial metrics to extract
TARGET_METRICS = [
    "Revenue",
    "Total Income",
    "EBITDA",
    "Profit After Tax",
    "PAT",
    "Net Profit",
    "Total Revenue",
    "Revenue from Operations",
    "Income",
    "Profit",
    "Loss",
    "Total Assets",
    "Net Worth",
    "Total Equity",
    "Total Liabilities",
    "Total Borrowings",
    "Borrowings",
    "Total equity and liabilities"
]


def _normalize_metric_name(metric_name: str) -> str:
    """
    Normalize metric name for matching.
    Converts to lowercase and removes extra whitespace.
    """
    return re.sub(r'\s+', ' ', metric_name.strip().lower())


def _is_target_metric(metric_name: str) -> bool:
    """
    Check if a metric name matches any target metric.
    Uses case-insensitive partial matching.
    """
    normalized = _normalize_metric_name(metric_name)
    
    for target in TARGET_METRICS:
        target_normalized = _normalize_metric_name(target)
        if target_normalized in normalized or normalized in target_normalized:
            return True
    
    return False


def extract_financial_metrics(extracted_json: dict) -> dict:
    """
    Extract explicit financial metrics from extracted JSON.
    
    Args:
        extracted_json: Dictionary containing:
            - pages: List of page objects with text
            - tables: List of table objects with data
    
    Returns:
        Dictionary with structure:
        {
            "financial_summary": {
                "Revenue": {
                    "statement": "Table name",
                    "values": [
                        {"year": "FY23", "value": "182,678.57", "source": "prospectus"}
                    ],
                    "status": "raw"
                }
            },
            "confidence": "high (rule-based, no inference)"
        }
    
    IMPORTANT:
    - All numeric values remain as strings
    - No computation or inference
    - Only explicitly present metrics are extracted
    """
    
    financial_summary = {}
    
    # Extract from tables
    tables = extracted_json.get("tables", [])
    
    for table in tables:
        table_data = table.get("data", [])
        
        if not table_data or len(table_data) < 2:
            continue
        
        # First row is typically headers (years)
        headers = table_data[0]
        
        # Identify year columns (skip first column which is usually metric name)
        year_columns = []
        for idx, header in enumerate(headers[1:], start=1):
            # Look for year patterns: FY23, FY 2023, 2023, etc.
            if re.search(r'(FY|fy)?\s?\d{2,4}', str(header)):
                year_columns.append((idx, header.strip()))
        
        # Process each row
        for row in table_data[1:]:
            if not row or len(row) < 1:
                continue
            
            metric_name = row[0].strip()
            
            # Check if this is a target metric
            if not _is_target_metric(metric_name):
                continue
            
            # Extract values for each year
            values = []
            for col_idx, year_label in year_columns:
                if col_idx < len(row):
                    value = row[col_idx].strip()
                    
                    # Only include non-empty values
                    if value and value != "-" and value != "":
                        values.append({
                            "year": year_label,
                            "value": value,  # Keep as string
                            "source": "prospectus"
                        })
            
            # Store in summary if we found values
            if values:
                # Use original metric name as key
                if metric_name not in financial_summary:
                    financial_summary[metric_name] = {
                        "statement": f"Table on page {table.get('page_number', 'unknown')}",
                        "values": values,
                        "status": "raw"
                    }
                else:
                    # Append values if metric appears in multiple tables
                    financial_summary[metric_name]["values"].extend(values)
    
    return {
        "financial_summary": financial_summary,
        "metrics_found": len(financial_summary),
        "confidence": "high (rule-based, no inference)"
    }


