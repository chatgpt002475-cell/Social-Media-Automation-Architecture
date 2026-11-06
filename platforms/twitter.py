"""Twitter / X API v2 adapter."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class TwitterAdapter(BasePlatformAdapter):
    """Publishes tweets to X (Twitter) via API v2."""

    def __init__(self) -> None:
        super().__init__("twitter")
        self.api_key = settings.TWITTER_API_KEY
        self.access_token = settings.TWITTER_ACCESS_TOKEN

    def is_configured(self) -> bool:
        return bool(self.api_key and self.access_token)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        tw_content = post_data.get("content", {}).get("twitter", {})
        tweet_text = tw_content.get("tweet", "")
        thread_followup = tw_content.get("thread_followup", "")

        if not self.is_configured():
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "Twitter/X credentials not configured. Executed in local mock mode.",
                "payload": {
                    "tweet": tweet_text,
                    "thread_followup": thread_followup,
                    "media": media_path,
                },
            }

        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": tweet_text[:280]}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code in (200, 201):
                return {
                    "status": "success",
                    "platform": self.platform_name,
                    "response": resp.json(),
                }
            return {
                "status": "failed",
                "platform": self.platform_name,
                "error": resp.text,
                "status_code": resp.status_code,
            }
        except Exception as e:
            return {"status": "failed", "platform": self.platform_name, "error": str(e)}
