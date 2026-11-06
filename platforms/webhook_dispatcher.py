"""Webhook Dispatcher for Make.com, n8n, and Zapier automation engines."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class WebhookDispatcher(BasePlatformAdapter):
    """Dispatches generated content to external automation webhooks."""

    def __init__(self) -> None:
        super().__init__("webhook")
        self.make_url = settings.MAKE_WEBHOOK_URL
        self.n8n_url = settings.N8N_WEBHOOK_URL
        self.custom_url = settings.CUSTOM_WEBHOOK_URL

    def is_configured(self) -> bool:
        return bool(self.make_url or self.n8n_url or self.custom_url)

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        targets = []
        if self.make_url:
            targets.append(("Make.com", self.make_url))
        if self.n8n_url:
            targets.append(("n8n", self.n8n_url))
        if self.custom_url:
            targets.append(("Custom Webhook", self.custom_url))

        if not targets:
            return {
                "status": "mock_success",
                "platform": self.platform_name,
                "message": "No webhook URLs configured (MAKE_WEBHOOK_URL or N8N_WEBHOOK_URL in .env).",
                "payload_ready": True,
            }

        results = {}
        payload = {
            "post_id": post_data.get("id"),
            "brand_id": post_data.get("brand_id"),
            "topic": post_data.get("topic"),
            "content": post_data.get("content"),
            "media_path": media_path,
        }

        for name, url in targets:
            try:
                resp = requests.post(url, json=payload, timeout=15)
                results[name] = {
                    "status_code": resp.status_code,
                    "response": resp.text[:200],
                }
            except Exception as e:
                results[name] = {"error": str(e)}

        return {
            "status": "success",
            "platform": self.platform_name,
            "dispatches": results,
        }
