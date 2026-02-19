import os
import json

# ROOT data folder
DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

def extract_financial_metrics(structured_data: dict) -> dict:
    """
    TEMP PLACEHOLDER.
    Replace body with your actual financial metrics logic.
    """
    return {
        "company": structured_data.get("company", "unknown"),
        "raw_metrics": structured_data.get("financials", {}),
        "computed_metrics": structured_data.get("computed_metrics", {}),
        "source": "structured.json",
        "confidence": "derived_from_prospectus_data"
    }


def process_company(company_dir: str):
    extracted_dir = os.path.join(company_dir, "extracted")
    structured_path = os.path.join(extracted_dir, "structured.json")
    output_path = os.path.join(extracted_dir, "financial_metrics.json")

    if not os.path.exists(structured_path):
        print(f"⏭️  Skipping (no structured.json): {company_dir}")
        return

    if os.path.exists(output_path):
        print(f"✅ Already exists, skipping: {output_path}")
        return

    try:
        with open(structured_path, "r", encoding="utf-8") as f:
            structured_data = json.load(f)

        metrics = extract_financial_metrics(structured_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        print(f"✅ Metrics written: {output_path}")

    except Exception as e:
        print(f"❌ Error in {company_dir}: {e}")


def main():
    for company in os.listdir(DATA_ROOT):
        company_dir = os.path.join(DATA_ROOT, company)

        if not os.path.isdir(company_dir):
            continue

        process_company(company_dir)


if __name__ == "__main__":
    main()
