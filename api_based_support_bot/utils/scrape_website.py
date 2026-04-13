import sqlite3
import time
from playwright.sync_api import sync_playwright
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URLS = [
    "https://mahafyjcadmissions.in/landing",
    "https://mahafyjcadmissions.in/faqs",
    "https://mahafyjcadmissions.in/downloads",
    "https://mahafyjcadmissions.in/brochuremanuals",
    "https://mahafyjcadmissions.in/admissionschedule",
    "https://mahafyjcadmissions.in/careerpath",
    "https://mahafyjcadmissions.in/about-us",
    "https://mahafyjcadmissions.in/contact-us"
]

DB_NAME = "website_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pages
                 (url TEXT PRIMARY KEY, title TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def scrape_with_playwright():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for url in URLS:
            logger.info(f"Scraping {url} with Playwright...")
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                # Wait for any specific element if needed, but networkidle is good for SPAs
                time.sleep(2) # Extra buffer for JS rendering
                
                title = page.title()
                # Get the whole page text content
                content = page.evaluate("() => document.body.innerText")
                
                if content:
                    c.execute("INSERT OR REPLACE INTO pages (url, title, content) VALUES (?, ?, ?)",
                              (url, title, content.strip()))
                    logger.info(f"Saved {url}")
                else:
                    logger.warning(f"No content found for {url}")
                    
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
            
            time.sleep(1)

        browser.close()

    conn.commit()
    conn.close()
    logger.info("Scraping complete.")

if __name__ == "__main__":
    scrape_with_playwright()
