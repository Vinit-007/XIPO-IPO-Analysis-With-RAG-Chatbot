import json
import os
import sys
import re

# Handle import both when run directly and when imported from Flask app
try:
    from financial_metrics.metrics_computation import normalize_raw_metrics, compute_metrics
except ImportError:
    from metrics_computation import normalize_raw_metrics, compute_metrics

def process_financial_metrics(input_json, output_json):
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle multiple possible structures:
    # 1. data["raw_metrics"]
    # 2. data["financial_summary"]
    # 3. data["financial_analysis"]["financial_summary"]
    raw_metrics = (
        data.get("raw_metrics") or 
        data.get("financial_summary") or 
        data.get("financial_analysis", {}).get("financial_summary", {})
    )
    
    company = data.get("company", "unknown")
    
    # Extract Sector from structured analysis if available
    sector = "General"
    try:
        # Check if we have analysis data in input or separate file
        analysis_data = data
        
        # If input is financial_metrics.json, try to find sibling structured_analysis.json
        if "sections" not in data and "extracted" in os.path.dirname(input_json):
            analysis_path = os.path.join(os.path.dirname(input_json), "structured_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    analysis_data = json.load(f)
        
        # Parse Sector from IPO Overview
        if "sections" in analysis_data and "ipo_overview" in analysis_data["sections"]:
            overview_text = analysis_data["sections"]["ipo_overview"].get("content", "")
            # Regex to find "Sector: Value" or "Sector / Industry: Value"
            match = re.search(r'(?:Sector|Industry|Business Model)\s*(?:/|\\)?\s*(?:Industry)?\s*:?\s*([^\n\r]+)', overview_text, re.IGNORECASE)
            if match:
                sector_text = match.group(1).strip().strip(".*`")
                # Cleanup common artifacts
                if len(sector_text) > 2 and "not disclosed" not in sector_text.lower():
                    sector = sector_text
                    print(f"✅ Extracted Sector: {sector}")
    except Exception as e:
        print(f"⚠️ Sector extracted failed: {e}")

    normalized = normalize_raw_metrics(raw_metrics)
    computed = compute_metrics(normalized)

    final = {
        "company": company,
        "sector": sector,
        "normalized_metrics_crore": normalized,
        "computed_metrics": computed,
        "confidence": "unit-normalized-and-recomputed"
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2)

    print("✅ Financial metrics fixed & normalized")
    return final


if __name__ == "__main__":
    import os
    import glob
    
    # Auto-detect input file
    base_dir = "data/meesho/extracted"
    
    # Priority: financial_metrics.json > *_analysis.json
    fin_metrics = os.path.join(base_dir, "financial_metrics.json")
    if os.path.exists(fin_metrics):
        input_file = fin_metrics
    else:
        # Fallback to *_analysis.json
        analysis_files = glob.glob(os.path.join(base_dir, "*_analysis.json"))
        if analysis_files:
            input_file = analysis_files[0]
        else:
            print("❌ No input file found!")
            exit(1)
    
    print(f"📂 Using input: {input_file}")
    process_financial_metrics(
        input_file,
        os.path.join(base_dir, "financial_metrics_clean.json")
    )
