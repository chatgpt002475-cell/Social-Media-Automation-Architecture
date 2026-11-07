"""Application settings and configuration loader."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Global configuration settings."""

    # Paths
    BASE_DIR: Path = BASE_DIR
    CONFIG_DIR: Path = BASE_DIR / "config"
    DATA_DIR: Path = BASE_DIR / "data"
    OUTPUTS_DIR: Path = BASE_DIR / "outputs"
    IMAGES_OUTPUT_DIR: Path = OUTPUTS_DIR / "images"
    OLX_OUTPUT_DIR: Path = OUTPUTS_DIR / "olx"
    CALENDAR_OUTPUT_DIR: Path = OUTPUTS_DIR / "calendars"
    DB_PATH: Path = DATA_DIR / "automation.sqlite3"
    BRANDS_FILE: Path = CONFIG_DIR / "brands.json"

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Local Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "5000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "social-media-automation-secret")
    SCHEDULER_INTERVAL_SECONDS: int = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))

    # Webhooks
    MAKE_WEBHOOK_URL: str = os.getenv("MAKE_WEBHOOK_URL", "")
    N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "")
    CUSTOM_WEBHOOK_URL: str = os.getenv("CUSTOM_WEBHOOK_URL", "")

    # Meta (Facebook & Instagram)
    FB_PAGE_ID: str = os.getenv("FB_PAGE_ID", "")
    FB_PAGE_ACCESS_TOKEN: str = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    IG_USER_ID: str = os.getenv("IG_USER_ID", "")
    IG_ACCESS_TOKEN: str = os.getenv("IG_ACCESS_TOKEN", "")

    # LinkedIn
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    LINKEDIN_AUTHOR_URN: str = os.getenv("LINKEDIN_AUTHOR_URN", "")

    # Twitter / X
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_SECRET: str = os.getenv("TWITTER_ACCESS_SECRET", "")

    # Pinterest
    PINTEREST_ACCESS_TOKEN: str = os.getenv("PINTEREST_ACCESS_TOKEN", "")
    PINTEREST_BOARD_ID: str = os.getenv("PINTEREST_BOARD_ID", "")

    def __init__(self) -> None:
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        for directory in [
            self.DATA_DIR,
            self.OUTPUTS_DIR,
            self.IMAGES_OUTPUT_DIR,
            self.OLX_OUTPUT_DIR,
            self.CALENDAR_OUTPUT_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_brands(self) -> Dict[str, Any]:
        """Load brand profiles from JSON."""
        if not self.BRANDS_FILE.exists():
            return {}
        with open(self.BRANDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_brand(self, brand_id: str) -> Dict[str, Any] | None:
        """Get a single brand profile by ID."""
        brands = self.get_brands()
        return brands.get(brand_id)

    def save_brand(self, brand_id: str, brand_data: Dict[str, Any]) -> None:
        """Add or update a brand profile."""
        brands = self.get_brands()
        brands[brand_id] = brand_data
        with open(self.BRANDS_FILE, "w", encoding="utf-8") as f:
            json.dump(brands, f, indent=2, ensure_ascii=False)


settings = Settings()
