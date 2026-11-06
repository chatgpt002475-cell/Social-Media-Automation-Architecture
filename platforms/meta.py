"""Meta (Facebook Page & Instagram Business) publishing adapter."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class FacebookAdapter(BasePlatformAdapter):
    """Publishes to Facebook Business Page via Meta Graph API."""

    def __init__(self) -> None:
        super().__init__("facebook")
        self.page_id = settings.FB_PAGE_ID
        self.access_token = settings.FB_PAGE_ACCESS_TOKEN
        self.api_version = "v19.0"

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        fb_content = post_data.get("content", {}).get("facebook", {})
        message = fb_content.get("caption", "")
        hashtags = " ".join(fb_content.get("hashtags", []))
        full_text = f"{message}\n\n{hashtags}".strip()

        if not self.is_configured():
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "Facebook credentials not configured. Executed in local mock mode.",
                "payload": {"text": full_text, "media": media_path},
            }

        url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}/feed"
        payload = {"message": full_text, "access_token": self.access_token}

        try:
            resp = requests.post(url, data=payload, timeout=20)
            data = resp.json()
            if resp.status_code == 200:
                return {
                    "status": "success",
                    "platform": self.platform_name,
                    "post_id": data.get("id"),
                    "response": data,
                }
            return {
                "status": "failed",
                "platform": self.platform_name,
                "error": data.get("error", {}).get("message", "Unknown FB error"),
                "raw": data,
            }
        except Exception as e:
            return {"status": "failed", "platform": self.platform_name, "error": str(e)}


class InstagramAdapter(BasePlatformAdapter):
    """Publishes to Instagram Professional account via Instagram Graph API."""

    def __init__(self) -> None:
        super().__init__("instagram")
        self.ig_user_id = settings.IG_USER_ID
        self.access_token = settings.IG_ACCESS_TOKEN
        self.api_version = "v19.0"

    def is_configured(self) -> bool:
        return bool(self.ig_user_id and self.access_token)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        ig_content = post_data.get("content", {}).get("instagram", {})
        caption = ig_content.get("caption", "")
        hashtags = " ".join(ig_content.get("hashtags", []))
        full_caption = f"{caption}\n\n{hashtags}".strip()

        if not self.is_configured():
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "Instagram credentials not configured. Executed in local mock mode.",
                "payload": {
                    "caption": full_caption,
                    "media": media_path,
                    "carousel_slides": ig_content.get("carousel_slides", []),
                },
            }

        # Live Instagram Graph API container creation & publishing
        try:
            # Step 1: Create media container
            container_url = f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}/media"
            params = {
                "caption": full_caption,
                "access_token": self.access_token,
            }
            if media_path and media_path.startswith("http"):
                params["image_url"] = media_path

            resp = requests.post(container_url, data=params, timeout=20)
            res_data = resp.json()
            creation_id = res_data.get("id")

            if not creation_id:
                return {
                    "status": "failed",
                    "platform": self.platform_name,
                    "error": res_data.get("error", "Container creation failed"),
                }

            # Step 2: Publish media container
            publish_url = (
                f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}/media_publish"
            )
            pub_resp = requests.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=20,
            )
            return {
                "status": "success",
                "platform": self.platform_name,
                "response": pub_resp.json(),
            }
        except Exception as e:
            return {"status": "failed", "platform": self.platform_name, "error": str(e)}
