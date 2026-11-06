"""Abstract base platform adapter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BasePlatformAdapter(ABC):
    """Base class for all social media and marketplace distribution adapters."""

    def __init__(self, platform_name: str) -> None:
        self.platform_name = platform_name

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if required API credentials exist."""
        pass

    @abstractmethod
    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish or dispatch content to the platform."""
        pass
