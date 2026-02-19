import os
import json
import logging
from datetime import datetime

# Import existing tools
from tools.sebi_scraper import resolve_sebi_entity_name, extract_pdf_from_detail, download_pdf
from tools.rhp_extractor import extract_rhp_to_json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DisclosureAgent")

class DisclosureUpdateAgent:
    def __init__(self, company_name, base_dir):
        self.company_name = company_name
        self.base_dir = base_dir
        self.extracted_dir = os.path.join(base_dir, "extracted")
        self.structured_json_path = os.path.join(self.extracted_dir, "structured.json")
        self.processed_files = []

    def check_and_update(self):
        """
        Main entry point: Checks for updates, downloads, extracts, and merges.
        Returns:
            dict: Summary of actions taken
        """
        logger.info(f"🕵️ Checking for disclosures for: {self.company_name}")
        
        if not os.path.exists(self.structured_json_path):
            logger.warning("⚠️ No structured.json found. Skipping update check.")
            return {"status": "skipped", "reason": "no_base_data"}

        # 1. Local Check
        if self._local_update_exists():
            logger.info("✅ Updates already processed locally.")
            return {"status": "no_update_needed", "reason": "local_files_exist"}

        # 2. External Search
        updates = self._search_sebi_updates()
        if not updates:
            logger.info("✅ No new addendum/corrigendum found online.")
            return {"status": "no_update_found"}

        # 3. Process Updates
        actions = []
        for title, url in updates:
            doc_type = "corrigendum" if "corrigendum" in title.lower() else "addendum"
            result = self._process_document(title, url, doc_type)
            if result:
                actions.append(result)

        return {"status": "completed", "updates_processed": len(actions), "details": actions}

    def _local_update_exists(self):
        """Check if addendum/corrigendum JSONs exist."""
        # Simple check: if any *new* disclosure files exist. 
        # Ideally we check a log, but file existence is a good proxy for idempotency.
        # We look for 'addendum.json' or 'corrigendum.json' etc.
        # But there could be multiple. We'll stick to a simple check for now.
        return (os.path.exists(os.path.join(self.extracted_dir, "addendum.json")) or 
                os.path.exists(os.path.join(self.extracted_dir, "corrigendum.json")))

    def _search_sebi_updates(self):
        """Search SEBI for Addendum/Corrigendum."""
        candidates = resolve_sebi_entity_name(self.company_name)
        updates = []
        
        for title, url in candidates:
            title_lower = title.lower()
            # Validation Logic: Must mention Addendum/Corrigendum AND Company Name
            # (Company name check is implicit in resolve_sebi_entity_name usually, but good to double check)
            if ("addendum" in title_lower or "corrigendum" in title_lower):
                # Ensure it's not the RHP itself (though titles usually distinct)
                updates.append((title, url))
        
        return updates

    def _process_document(self, title, detail_url, doc_type):
        """Download, Extract, and Merge."""
        logger.info(f"⬇️ Found {doc_type}: {title}")
        
        # 1. Get PDF URL
        pdf_url = extract_pdf_from_detail(detail_url)
        if not pdf_url:
            return None

        # 2. Download
        filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
        save_path = os.path.join(self.base_dir, "rhp", filename) # Save alongside RHP
        
        if not os.path.exists(save_path):
            try:
                download_pdf(pdf_url, save_path)
            except Exception as e:
                logger.error(f"Failed to download {title}: {e}")
                return None

        # 3. Extract
        json_filename = f"{doc_type}.json" # Simplified for single instances per type for now
        json_path = os.path.join(self.extracted_dir, json_filename)
        
        try:
            extract_rhp_to_json(save_path, json_path)
        except Exception as e:
            logger.error(f"Failed to extract {title}: {e}")
            return None

        # 4. Merge
        self._merge_update(json_path, doc_type, title)
        
        return {"type": doc_type, "file": filename, "status": "merged"}

    def _merge_update(self, update_json_path, doc_type, title):
        """Merge extracted update into structured.json."""
        with open(self.structured_json_path, "r", encoding="utf-8") as f:
            base_data = json.load(f)
            
        with open(update_json_path, "r", encoding="utf-8") as f:
            update_data = json.load(f)

        # Create Update Log Entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": doc_type,
            "source_title": title,
            "pages_added": update_data.get("total_pages", 0),
            "original_file": base_data.get("source_file")
        }

        # Initialize update log if missing
        if "update_log" not in base_data:
            base_data["update_log"] = []
        
        base_data["update_log"].append(log_entry)

        # Merge Strategy
        # 1. Append Pages (Addendum adds info)
        # We prepend or append? Usually updates are relevant context, so we append to pages list.
        # But we must tag them.
        new_pages = update_data.get("pages", [])
        for page in new_pages:
            page["source_type"] = doc_type
            page["page_number"] = f"{doc_type}_{page['page_number']}" # Unique ID
        
        base_data["pages"].extend(new_pages)

        # 2. Append Tables
        new_tables = update_data.get("tables", [])
        base_data["tables"].extend(new_tables)
        
        # 3. Corrigendum Specifics (Overrides)
        # Identifying specific field overrides is hard without semantic understanding.
        # For Phase 2, we append the text so RAG can find the "Corrected" version.
        # To truly "Override", we would need to know exactly which old value to delete.
        # Instead, we rely on RAG retrieving the latest info (Addendum) if we weight it or prompts handle it.
        # We explicitly add a "LATEST_UPDATES" section to the start of the pages list? 
        # No, appending with source_type allows RAG to filter/prioritize.

        with open(self.structured_json_path, "w", encoding="utf-8") as f:
            json.dump(base_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"✅ Merged {doc_type} into structured.json")


def run_disclosure_check(company_name, base_dir):
    """Wrapper function for pipeline integration."""
    agent = DisclosureUpdateAgent(company_name, base_dir)
    return agent.check_and_update()
