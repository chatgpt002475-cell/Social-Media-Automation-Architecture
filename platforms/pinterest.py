"""Pinterest publishing adapter."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class PinterestAdapter(BasePlatformAdapter):
    """Publishes to Pinterest boards via Pinterest API v5."""

    def __init__(self) -> None:
        super().__init__("pinterest")
        self.access_token = settings.PINTEREST_ACCESS_TOKEN
        self.board_id = settings.PINTEREST_BOARD_ID

    def is_configured(self) -> bool:
        return bool(self.access_token and self.board_id)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        pin_content = post_data.get("content", {}).get("pinterest", {})
        title = pin_content.get("title", "")
        description = pin_content.get("description", "")
        link = post_data.get("content", {}).get("facebook", {}).get("link", "")

        if not self.is_configured():
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "Pinterest credentials not configured. Executed in local mock mode.",
                "payload": {
                    "title": title,
                    "description": description,
                    "board": pin_content.get("board", ""),
                    "media": media_path,
                },
            }

        url = "https://api.pinterest.com/v5/pins"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "board_id": self.board_id,
            "title": title[:100],
            "description": description[:500],
            "link": link or "https://example.com",
        }

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
