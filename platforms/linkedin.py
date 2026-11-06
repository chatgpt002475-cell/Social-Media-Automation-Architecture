"""LinkedIn publishing adapter."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class LinkedInAdapter(BasePlatformAdapter):
    """Publishes to LinkedIn Company Pages or Profiles."""

    def __init__(self) -> None:
        super().__init__("linkedin")
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.author_urn = settings.LINKEDIN_AUTHOR_URN

    def is_configured(self) -> bool:
        return bool(self.access_token and self.author_urn)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        li_content = post_data.get("content", {}).get("linkedin", {})
        post_body = li_content.get("post_body", "")
        hashtags = " ".join(li_content.get("hashtags", []))
        full_text = f"{post_body}\n\n{hashtags}".strip()

        if not self.is_configured():
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "LinkedIn credentials not configured. Executed in local mock mode.",
                "payload": {
                    "text": full_text,
                    "headline": li_content.get("headline", ""),
                    "key_takeaways": li_content.get("key_takeaways", []),
                    "media": media_path,
                },
            }

        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": full_text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
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
