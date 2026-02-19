import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.sebi.gov.in"
LISTING_URL = (
    "https://www.sebi.gov.in/sebiweb/home/HomeAction.do"
    "?doListing=yes&sid=3&ssid=15&smid=11"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# -------------------------------------------------
# Fetch IPO listing detail pages from SEBI
# -------------------------------------------------
def resolve_sebi_entity_name(query: str, max_pages: int = 5, max_retries: int = 3):
    """Search SEBI filings with retry logic for unstable connections."""
    import time
    from requests.exceptions import RequestException
    
    results = []

    for page in range(max_pages):
        start = page * 25
        search_url = f"{LISTING_URL}&search={query}&start={start}"

        # Retry logic for search request
        for attempt in range(max_retries):
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=30)
                response.raise_for_status()
                break
            except RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"   ⚠️  Connection issue, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"   ❌ Failed to connect to SEBI after {max_retries} attempts")
                    return results

        soup = BeautifulSoup(response.text, "html.parser")

        found = False
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            href = a["href"]

            if title and "/filings/public-issues/" in href:
                results.append((title, urljoin(BASE_URL, href)))
                found = True

        if not found:
            break

    return results


# -------------------------------------------------
# Extract PDF link from IPO detail page
# -------------------------------------------------
def extract_pdf_from_detail(detail_url: str, max_retries: int = 3):
    """Extract PDF URL from detail page with retry logic."""
    import time
    from requests.exceptions import RequestException
    
    # Retry logic for detail page request
    for attempt in range(max_retries):
        try:
            response = requests.get(detail_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            break
        except RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"   ⚠️  Connection issue, retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"   ❌ Failed to fetch detail page after {max_retries} attempts")
                return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Primary method — iframe viewer
    iframe = soup.find("iframe", src=True)
    if iframe and "file=" in iframe["src"]:
        match = re.search(r"file=(https?://[^\s&]+\.pdf)", iframe["src"])
        if match:
            return match.group(1)

    # Fallback — direct PDF links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            return urljoin(BASE_URL, href)

    return None


# -------------------------------------------------
# Download PDF with retry and resume capability
# -------------------------------------------------
def download_pdf(pdf_url: str, save_path: str, max_retries: int = 5):
    """Download PDF with automatic retry and resume on connection failures."""
    import time
    from requests.exceptions import ChunkedEncodingError, ConnectionError
    
    for attempt in range(max_retries):
        try:
            # Check if partial file exists
            resume_pos = 0
            if os.path.exists(save_path):
                resume_pos = os.path.getsize(save_path)
                if resume_pos > 0:
                    print(f"   📂 Resuming from {resume_pos / (1024*1024):.1f} MB")
            
            # Set up headers for resume
            headers = HEADERS.copy()
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            # Make request
            r = requests.get(pdf_url, headers=headers, stream=True, timeout=120)
            r.raise_for_status()
            
            # Get total size
            total_size = int(r.headers.get('content-length', 0))
            if resume_pos > 0:
                total_size += resume_pos
            
            # Download with progress
            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded = resume_pos
            
            with open(save_path, mode) as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Show progress every 1 MB
                        if downloaded % (1024 * 1024) < 8192:
                            progress = (downloaded / total_size * 100) if total_size > 0 else 0
                            print(f"   📥 {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({progress:.0f}%)", end='\r')
            
            print(f"\n   ✅ Download complete: {total_size / (1024*1024):.1f} MB")
            return
            
        except (ChunkedEncodingError, ConnectionError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                print(f"\n   ⚠️  Download interrupted: {type(e).__name__}")
                print(f"   🔄 Retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\n   ❌ Download failed after {max_retries} attempts")
                raise


# -------------------------------------------------
# Main public function
# -------------------------------------------------
def fetch_company_rhp(company_name: str):
    safe_name = company_name.replace(" ", "_")
    base_dir = f"data/{safe_name}/rhp"
    os.makedirs(base_dir, exist_ok=True)

    print("🔎 Resolving official SEBI entity name...")
    candidates = resolve_sebi_entity_name(company_name)

    if not candidates:
        print("❌ No matching SEBI entities found")
        return []

    print("✅ SEBI matched entities:")
    
    valid_candidates = []
    for title, url in candidates:
        # 1. Filter out Addendums/Corrigendums
        if "addendum" in title.lower() or "corrigendum" in title.lower():
            continue
        valid_candidates.append((title, url))

    if not valid_candidates:
        print("❌ No valid SEBI entities found (filtered out addendums)")
        return []

    # 2. Prioritize RHP or Exact Name
    selected_candidate = None
    
    # Priority A: Contains "RHP"
    for title, url in valid_candidates:
        if "rhp" in title.lower():
            selected_candidate = (title, url)
            break
    
    # Priority B: Exact Company Name (or very close) if no RHP found
    if not selected_candidate:
        for title, url in valid_candidates:
            if company_name.lower() in title.lower():
                selected_candidate = (title, url)
                break
    
    # Priority C: First valid if nothing else
    if not selected_candidate:
        selected_candidate = valid_candidates[0]

    # Print candidates for debugging
    for i, (title, _) in enumerate(valid_candidates, 1):
        print(f"   {i}. {title}")

    title, detail_url = selected_candidate
    print(f"🎯 Selected entity: {title}")

    pdf_url = extract_pdf_from_detail(detail_url)
    if not pdf_url:
        print("❌ RHP PDF not found")
        return []

    filename = pdf_url.split("/")[-1]
    save_path = os.path.join(base_dir, filename)

    if not os.path.exists(save_path):
        print(f"⬇️ Downloading RHP: {filename}")
        download_pdf(pdf_url, save_path)
        print("✅ Downloaded")

    return [save_path]
