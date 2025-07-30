# src/config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

SESSION_FILE = os.getenv(
    "SESSION_FILE",
    str(Path.home() / ".linkedin_scraper_session.json")
)

DEFAULT_DB = f"sqlite:///{BASE_DIR / 'linkedin.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)

PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("1","true","yes")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("linkedin-scraper")
