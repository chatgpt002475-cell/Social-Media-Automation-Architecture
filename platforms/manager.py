"""Unified platform manager and distribution orchestrator."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.database import db
from platforms.base import BasePlatformAdapter
from platforms.linkedin import LinkedInAdapter
from platforms.meta import FacebookAdapter, InstagramAdapter
from platforms.olx import OLXAdapter
from platforms.pinterest import PinterestAdapter
from platforms.twitter import TwitterAdapter
from platforms.webhook_dispatcher import WebhookDispatcher

logger = logging.getLogger(__name__)


class PlatformManager:
    """Manages dispatch and multi-platform publishing."""

    def __init__(self) -> None:
        self.adapters: Dict[str, BasePlatformAdapter] = {
            "facebook": FacebookAdapter(),
            "instagram": InstagramAdapter(),
            "linkedin": LinkedInAdapter(),
            "pinterest": PinterestAdapter(),
            "twitter": TwitterAdapter(),
            "olx": OLXAdapter(),
            "webhook": WebhookDispatcher(),
        }

    def get_supported_platforms(self) -> List[str]:
        return list(self.adapters.keys())

    def get_platform_status(self) -> Dict[str, bool]:
        """Check configuration status of each platform adapter."""
        return {name: adapter.is_configured() for name, adapter in self.adapters.items()}

    def publish_post(
        self,
        post_data: Dict[str, Any],
        target_platforms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publish a post to specified platforms, record logs, and update status."""
        post_id = post_data.get("id") or post_data.get("post_id", "unknown")
        brand_id = post_data.get("brand_id", "general")
        images = post_data.get("images", {})

        if not target_platforms:
            target_platforms = ["facebook", "instagram", "linkedin", "olx"]

        # If webhooks configured, include webhook automatically
        if self.adapters["webhook"].is_configured() and "webhook" not in target_platforms:
            target_platforms.append("webhook")

        execution_results: Dict[str, Any] = {}
        all_success = True

        for platform_name in target_platforms:
            adapter = self.adapters.get(platform_name.lower())
            if not adapter:
                logger.warning(f"No adapter registered for platform: {platform_name}")
                continue

            # Pick matching image for platform
            media_path = None
            if platform_name in ("instagram", "facebook"):
                media_path = images.get("portrait") or images.get("square")
            elif platform_name == "linkedin":
                media_path = images.get("landscape") or images.get("square")
            elif platform_name == "pinterest":
                media_path = images.get("pinterest") or images.get("square")
            else:
                media_path = images.get("square") or images.get("landscape")

            try:
                res = adapter.publish(post_data=post_data, media_path=media_path)
                execution_results[platform_name] = res

                # Determine log status
                status = res.get("status", "unknown")
                if status == "failed":
                    all_success = False

                # Record in database log
                db.log_publish(
                    post_id=post_id,
                    brand_id=brand_id,
                    platform=platform_name,
                    status=status,
                    response_payload=res,
                )
            except Exception as e:
                all_success = False
                err_msg = str(e)
                execution_results[platform_name] = {"status": "failed", "error": err_msg}
                db.log_publish(
                    post_id=post_id,
                    brand_id=brand_id,
                    platform=platform_name,
                    status="failed",
                    response_payload={"error": err_msg},
                )

        # Update post status
        final_status = "published" if all_success else "partially_published"
        db.update_post_status(post_id, final_status)

        return {
            "post_id": post_id,
            "overall_status": final_status,
            "platform_results": execution_results,
        }


platform_manager = PlatformManager()
