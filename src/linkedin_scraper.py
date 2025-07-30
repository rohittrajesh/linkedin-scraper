# src/linkedin_scraper.py

import os
from datetime import datetime
from playwright.sync_api import BrowserContext, sync_playwright
from src.config import PLAYWRIGHT_HEADLESS, SESSION_FILE, logger

_playwright = None 

def ensure_logged_in() -> BrowserContext:
    """
    Starts Playwright, restores or saves session, and returns an authenticated context.
    """
    global _playwright
    _playwright = sync_playwright().start()
    browser = _playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
    context = browser.new_context()

    if os.path.exists(SESSION_FILE):
        logger.info(f"Restoring session from {SESSION_FILE}")
        context.set_storage_state(path=SESSION_FILE)

    page = context.new_page()
    page.goto("https://www.linkedin.com/feed", wait_until="networkidle")
    if "login" in page.url:
        logger.info("Not logged in—please log in manually in the browser.")
        page.pause()  
        context.storage_state(path=SESSION_FILE)
        logger.info(f"Saved new session to {SESSION_FILE}")
    else:
        logger.info("Session valid; no login needed.")

    return context

def fetch_profile_info(context: BrowserContext, profile_url: str) -> dict:
    """
    Given an authenticated BrowserContext and a profile URL,
    navigate to the page and extract:
      - url, name, headline, location, email, phone
    """
    page = context.new_page()
    page.goto(profile_url, wait_until="networkidle")
    logger.info(f"Scraping profile info from {profile_url}")

    # ─── Basic fields (selectors may need tweaks!) ─────────────────────────────────
    name = page.locator("h1.text-heading-xlarge").inner_text().strip()
    headline = page.locator("div.text-body-medium.break-words").inner_text().strip()
    location = page.locator("span.text-body-small.inline.t-black--light").inner_text().strip()

    # ─── Contact Info ────────────────────────────────────────────────────────────────
    email = None
    phone = None
    try:
        page.click("a[data-control-name='contact_see_more']", timeout=5000)
        page.wait_for_selector("section.pv-contact-info", timeout=5000)
        email_elem = page.locator("section.pv-contact-info a[href^='mailto:']").first
        email = email_elem.get_attribute("href").replace("mailto:", "") if email_elem else None
        phone_elem = page.locator("section.pv-contact-info span.t-14").first
        phone = phone_elem.inner_text().strip() if phone_elem else None
    except Exception:
        logger.debug("No contact info found or failed to load.")

    page.close()
    return {
        "url":      profile_url,
        "name":     name,
        "headline": headline,
        "location": location,
        "email":    email,
        "phone":    phone,
    }

def fetch_all_posts(context: BrowserContext, profile_url: str) -> list[dict]:
    """
    Scrape ALL posts from the profile’s Activity → Posts page.
    Returns a list of dicts [{ post_url, content, posted_at }, …].
    """
    activity_url = profile_url.rstrip("/") + "/detail/recent-activity/shares/"
    page = context.new_page()
    page.goto(activity_url, wait_until="networkidle")
    logger.info(f"Scraping posts from {activity_url}")

    # ─── Infinite scroll until no more new posts ────────────────────────────────────
    last_height = page.evaluate("() => document.body.scrollHeight")
    while True:
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        new_height = page.evaluate("() => document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    posts = []
    cards = page.locator("div.occludable-update")
    for i in range(cards.count()):
        card = cards.nth(i)
        content = card.locator("div.feed-shared-update-v2__description").inner_text().strip()
        link_elem = card.locator("a.app-aware-link").first
        post_url  = link_elem.get_attribute("href") if link_elem else None

        # Timestamp parsing could go here; for now we set UTC now
        posts.append({
            "post_url":  post_url,
            "content":   content,
            "posted_at": datetime.utcnow(),
        })

    page.close()
    return posts