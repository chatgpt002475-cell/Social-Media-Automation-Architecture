"""Meta (Facebook Page & Instagram Business) publishing adapter."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


def _ensure_public_url(media_path: Optional[str]) -> Optional[str]:
    """Ensure image is an accessible public HTTPS URL for Meta's servers.
    If it's a local file, upload it temporarily to catbox so Meta Graph API can download it."""
    if not media_path:
        return None
    if media_path.startswith("http://") or media_path.startswith("https://"):
        return media_path

    local_path = Path(media_path)
    if not local_path.is_absolute():
        local_path = (settings.BASE_DIR / media_path.lstrip("/")).resolve()

    if local_path.exists() and local_path.is_file():
        try:
            with open(local_path, "rb") as f:
                r = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=15,
                )
            if r.status_code == 200 and r.text.strip().startswith("http"):
                return r.text.strip()
        except Exception as e:
            logger.warning(f"Failed to upload local image to public URL for Meta: {e}")
    return None


class FacebookAdapter(BasePlatformAdapter):
    """Publishes to Facebook Business Page via Meta Graph API."""

    def __init__(self) -> None:
        super().__init__("facebook")
        self.page_id = settings.FB_PAGE_ID
        self.access_token = settings.FB_PAGE_ACCESS_TOKEN
        self.api_version = "v19.0"

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def verify_connection(self) -> Dict[str, Any]:
        """Verify Facebook Page API connection with Meta."""
        if not self.is_configured():
            return {
                "connected": False,
                "error": "FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN not configured in .env",
            }
        url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}"
        params = {
            "fields": "id,name,link",
            "access_token": self.access_token,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if r.status_code == 200 and "id" in data:
                return {
                    "connected": True,
                    "platform": "facebook",
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "link": data.get("link"),
                }
            return {
                "connected": False,
                "platform": "facebook",
                "error": data.get("error", {}).get("message", "Verification failed"),
                "raw": data,
            }
        except Exception as e:
            return {"connected": False, "platform": "facebook", "error": str(e)}

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

        # If image available, attach public URL
        public_img = _ensure_public_url(media_path)
        if public_img:
            url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}/photos"
            payload = {
                "caption": full_text,
                "url": public_img,
                "access_token": self.access_token,
            }

        try:
            resp = requests.post(url, data=payload, timeout=20)
            data = resp.json()
            if resp.status_code == 200:
                return {
                    "status": "success",
                    "platform": self.platform_name,
                    "post_id": data.get("id") or data.get("post_id"),
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

    def verify_connection(self) -> Dict[str, Any]:
        """Verify Instagram API connection with Meta."""
        if not self.is_configured():
            return {
                "connected": False,
                "error": "IG_USER_ID or IG_ACCESS_TOKEN not configured in .env",
            }
        url = f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}"
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count",
            "access_token": self.access_token,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if r.status_code == 200 and "id" in data:
                return {
                    "connected": True,
                    "platform": "instagram",
                    "id": data.get("id"),
                    "username": data.get("username"),
                    "name": data.get("name"),
                    "profile_picture_url": data.get("profile_picture_url"),
                }
            return {
                "connected": False,
                "platform": "instagram",
                "error": data.get("error", {}).get("message", "Verification failed"),
                "raw": data,
            }
        except Exception as e:
            return {"connected": False, "platform": "instagram", "error": str(e)}

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

        public_img_url = _ensure_public_url(media_path)
        if not public_img_url:
            return {
                "status": "failed",
                "platform": self.platform_name,
                "error": "Meta Instagram Graph API requires an image attachment. No valid image was generated or accessible.",
            }

        # Live Instagram Graph API container creation & publishing
        try:
            # Step 1: Create media container
            container_url = f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}/media"
            params = {
                "image_url": public_img_url,
                "caption": full_caption,
                "access_token": self.access_token,
            }

            resp = requests.post(container_url, data=params, timeout=25)
            res_data = resp.json()
            creation_id = res_data.get("id")

            if not creation_id:
                err_detail = res_data.get("error", {}).get("message", str(res_data))
                return {
                    "status": "failed",
                    "platform": self.platform_name,
                    "error": f"Container creation failed: {err_detail}",
                    "raw": res_data,
                }

            # Step 2: Publish media container
            publish_url = (
                f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}/media_publish"
            )
            pub_resp = requests.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=25,
            )
            pub_data = pub_resp.json()
            if pub_resp.status_code == 200 and "id" in pub_data:
                return {
                    "status": "success",
                    "platform": self.platform_name,
                    "instagram_post_id": pub_data.get("id"),
                    "image_url": public_img_url,
                    "response": pub_data,
                }
            return {
                "status": "failed",
                "platform": self.platform_name,
                "error": pub_data.get("error", {}).get("message", "Publishing failed"),
                "raw": pub_data,
            }
        except Exception as e:
            return {"status": "failed", "platform": self.platform_name, "error": str(e)}
