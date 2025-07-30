import os
from datetime import datetime
from playwright.sync_api import sync_playwright, BrowserContext
from src.config import PLAYWRIGHT_HEADLESS, SESSION_FILE, logger

_playwright = None

def ensure_logged_in() -> BrowserContext:
    """
    Starts Playwright, restores or saves session, and returns an authenticated context.
    """
    global _playwright
    _playwright = sync_playwright().start()
    browser = _playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)

    if os.path.exists(SESSION_FILE):
        logger.info(f"Restoring session from {SESSION_FILE}")
        context = browser.new_context(storage_state=SESSION_FILE)
    else:
        context = browser.new_context()

    page = context.new_page()
    page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded")
    if "login" in page.url:
        logger.info("Not logged in—please log in in the opened browser window.")
        input("👉 After logging in, press ENTER here to continue…")
        context.storage_state(path=SESSION_FILE)
        logger.info(f"Saved new session to {SESSION_FILE}")
    else:
        logger.info("Existing session is valid; no login needed.")

    return context


def fetch_profile_info(context: BrowserContext, profile_url: str) -> dict:
    """
    Navigate to PROFILE_URL and extract url, name, headline, location, email, phone.
    """
    page = context.new_page()
    page.goto(profile_url, wait_until="domcontentloaded")
    logger.info(f"Scraping profile info from {profile_url}")

    page.wait_for_selector("h1", timeout=15000)
    name_locator = page.locator("h1.text-heading-xlarge")
    try:
        if name_locator.count() > 0:
            name = name_locator.first.inner_text(timeout=5000).strip()
        else:
            name = page.locator("h1").first.inner_text(timeout=5000).strip()
    except:
        logger.warning("Failed to extract name; setting to empty.")
        name = ""

    headline = ""
    try:
        page.wait_for_selector("div.text-body-medium.break-words", timeout=10000)
        headline = page.locator("div.text-body-medium.break-words") \
                       .first.inner_text(timeout=5000).strip()
    except:
        logger.warning("Failed to extract headline; setting to empty.")

    location = ""
    try:
        page.wait_for_selector("span.text-body-small.inline.t-black--light", timeout=10000)
        location = page.locator("span.text-body-small.inline.t-black--light") \
                        .first.inner_text(timeout=5000).strip()
    except:
        logger.warning("Failed to extract location; setting to empty.")

    email = None
    phone = None
    try:
        page.click("a[data-control-name='contact_see_more']", timeout=5000)
        page.wait_for_selector("section.pv-contact-info", timeout=5000)
        em = page.locator("section.pv-contact-info a[href^='mailto:']").first
        if em: email = em.get_attribute("href").replace("mailto:", "").strip()
        ph = page.locator("section.pv-contact-info span.t-14").first
        if ph: phone = ph.inner_text().strip()
    except:
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

def fetch_all_posts(context: BrowserContext, profile_url: str, max_posts: int = 50) -> list[dict]:
    """
    Scrape up to max_posts from the profile’s Activity → Posts page.
    Returns a list of dicts [{ post_url, content, posted_at }, …].
    """
    activity_url = profile_url.rstrip("/") + "/detail/recent-activity/shares/"
    page = context.new_page()
    page.goto(activity_url, wait_until="domcontentloaded")
    logger.info(f"Scraping posts from {activity_url}")

    try:
        page.wait_for_selector("div.occludable-update", timeout=15000)
    except:
        logger.warning("No posts found on the activity page.")
        page.close()
        return []

    for _ in range(3):
        page.evaluate("window.scrollBy(0, window.innerHeight)")
        page.wait_for_timeout(1000)

    raw_posts = page.evaluate(f"""
      () => {{
        const cards = Array.from(
          document.querySelectorAll('div.occludable-update')
        ).slice(0, {max_posts});
        return cards.map(card => {{
          // First try the newer text‐view selector:
          let txtEl = card.querySelector("div.feed-shared-text__text-view span[dir='ltr']");
          // Fallback to the older description selector:
          if (!txtEl) txtEl = card.querySelector("div.feed-shared-update-v2__description");
          const content = txtEl ? txtEl.innerText.trim() : "";

          // Post URL is usually on the first app‐aware link in the header:
          const link = card.querySelector("a.app-aware-link");
          const post_url = link ? link.href : null;

          return {{ post_url, content }};
        }});
      }}
    """)

    posts = []
    for item in raw_posts:
        if not item["content"]:
            continue
        posts.append({
            "post_url":  item["post_url"],
            "content":   item["content"],
            "posted_at": datetime.utcnow(),
        })

    page.close()
    logger.info(f"Extracted {len(posts)} posts (attempted {len(raw_posts)}).")
    return posts