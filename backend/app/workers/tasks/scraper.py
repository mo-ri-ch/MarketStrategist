import logging
import re
from playwright.sync_api import sync_playwright
from app.workers.celery_app import celery_app

logger = logging.getLogger("market-strategist-scraper")

def clean_text(text: str) -> str:
    """
    Cleans up scraped body text by stripping redundant whitespace and blank lines.
    """
    # Replace multiple spaces with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace three or more newlines with double newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()

@celery_app.task(name="app.workers.tasks.scraper.scrape_website")
def scrape_website(url: str) -> str:
    """
    Background Celery task that navigates to a URL using a headless Chromium instance,
    extracts the page body's raw text, cleans it up, and returns it.
    """
    logger.info(f"Scraper task triggered for target: {url}")
    try:
        with sync_playwright() as p:
            # Launch Chromium with anti-bot headers/agent settings
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            # Navigate to the competitor page with a 30s timeout
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for 2 seconds to allow any client-side hydrated content to render
            page.wait_for_timeout(2000)
            
            # Extract raw body inner text
            raw_text = page.locator("body").inner_text()
            
            browser.close()
            
            if not raw_text:
                raise ValueError(f"Failed to scrape text: body was empty for {url}")
            
            cleaned = clean_text(raw_text)
            logger.info(f"Scrape successful: {len(cleaned)} cleaned characters gathered from {url}")
            return cleaned
            
    except Exception as e:
        logger.error(f"Error encountered during scrape of {url}: {e}")
        raise e
