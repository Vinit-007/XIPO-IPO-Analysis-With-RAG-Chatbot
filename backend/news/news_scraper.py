# ===================== IMPORTS =====================
import requests  # HTTP library for making web requests
from bs4 import BeautifulSoup  # HTML parsing library
from datetime import datetime  # Date and time manipulation
from urllib.parse import quote_plus  # URL encoding for special characters


# ===================== CONFIGURATION =====================
# HTTP headers to identify our scraper and avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (IPO Analyzer)"
}


# ===================== UTILITY FUNCTIONS =====================

# Clean text by removing extra whitespace and line breaks.
def _clean(text):
    return " ".join(text.split())



# Safely make HTTP GET request with error handling.
def _safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()  # Raise exception for HTTP errors
        return r.text
    except:
        return None




# Extract article summary by fetching full page and extracting paragraphs.
def _extract_summary(article_url):

    html = _safe_get(article_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")  # Find all paragraph tags
    paras = soup.find_all("p")
    lines = []

    # Extract meaningful paragraphs (>40 characters)
    for p in paras:
        txt = _clean(p.get_text())
        if len(txt) > 40:
            lines.append(txt)
        if len(lines) == 2:  # Limit to first 2 paragraphs
            break

    return " ".join(lines) if lines else None


# Import XML parser for RSS feed processing
import xml.etree.ElementTree as ET

# ===================== NEWS SOURCES =====================


# Scrape news via Google News RSS Feed.
def scrape_google_news_rss(query):

    # Google News RSS URL for India (en-IN)
    rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}+when:30d&hl=en-IN&gl=IN&ceid=IN:en"
    print(f"   [rss] Fetching: {rss_url}")
    
    try:
        # Make HTTP request to RSS feed
        response = requests.get(rss_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        articles = []
        
        # Import date parser for RSS timestamps
        from email.utils import parsedate_to_datetime
        
        # Iterate through each article item in RSS feed
        for item in root.findall(".//item"):
            # Extract article metadata
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source = item.find("source").text if item.find("source") is not None else "Google News"
            
            # Clean title (Google News often puts " - SourceName" at the end)
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
                
            # Skip articles without title or link
            if not title or not link:
                continue
            
            # Parse publication date and calculate days old
            days_old = 0
            formatted_date = datetime.today().strftime("%Y-%m-%d")
            
            if pub_date_str:
                try:
                    dt = parsedate_to_datetime(pub_date_str)
                    # Make offset-naive for comparison
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                        
                    delta = datetime.now() - dt
                    days_old = delta.days
                    formatted_date = dt.strftime("%Y-%m-%d")
                except:
                    pass
            
            # STRICT FILTER: Ignore news older than 20 days
            if days_old > 20:
                continue
                
            # Create article dictionary with metadata
            articles.append({
                "headline": title.strip(),
                "source": source.strip(),
                "url": link.strip(),
                "summary": f"Published: {formatted_date} ({days_old} days ago)", 
                "published_at": formatted_date,
                "days_old": days_old,
                "scraped_at": datetime.today().strftime("%Y-%m-%d")
            })
            
            # Limit to 15 articles to avoid overwhelming data
            if len(articles) >= 15:
                break
                
        return articles

    except Exception as e:
        print(f"   ❌ Google News RSS failed: {e}")
        return []


# ===================== LEGACY SCRAPERS =====================
# These are disabled but kept for potential future use

def scrape_moneycontrol(query):
    """Legacy MoneyControl scraper - disabled in favor of RSS."""
    return [] # Disabled to prioritize RSS

def scrape_economic_times(query):
    """Legacy Economic Times scraper - disabled in favor of RSS."""
    return [] # Disabled to prioritize RSS

def scrape_business_standard(query):
    """Legacy Business Standard scraper - disabled in favor of RSS."""
    return [] # Disabled to prioritize RSS

def scrape_livemint(query):
    """Legacy LiveMint scraper - disabled in favor of RSS."""
    return [] # Disabled to prioritize RSS



# ===================== MAIN ORCHESTRATOR =====================

# Main function to orchestrate news scraping for IPO analysis.
def scrape_ipo_news(company_name, sector=None):
    news = []
    
    print(f"   🔎 Searching news via Google News RSS for: {company_name}")
    
    # 1. Primary Search: Company Name + IPO (most relevant)
    # This targets IPO-specific announcements and news
    news.extend(scrape_google_news_rss(f"{company_name} IPO"))
    
    # 2. Secondary Search: Company Name (General)
    # Only if we don't have enough IPO-specific news
    if len(news) < 5:
         news.extend(scrape_google_news_rss(company_name))
    
    # 3. Sector Search (Context/Market Trends)
    # Provides broader market context for the IPO
    if sector:
        print(f"   🔎 Searching sector news via Google News RSS for: {sector}")
        sector_news = scrape_google_news_rss(f"{sector} sector India")
        
        # Mark sector news for relevance classification
        for n in sector_news:
            n['relevance'] = 'Sector'
        news.extend(sector_news)

    today = datetime.today().strftime("%Y-%m-%d")

    # ===================== DEDUPLICATION & FILTERING =====================
    seen_urls = set()
    unique_news = []
    
    for n in news:
        # Skip duplicate articles based on URL
        if n["url"] not in seen_urls:
            n["scraped_at"] = today
            
            # Determine relevance if not already set
            if 'relevance' not in n:
                if company_name.lower() in n['headline'].lower():
                    n['relevance'] = 'Company'  # Directly mentions the company
                else:
                    n['relevance'] = 'Related'  # Related but not directly about company
                
            unique_news.append(n)
            seen_urls.add(n["url"])

    # Return top 20 articles for comprehensive analysis
    return unique_news[:20]
