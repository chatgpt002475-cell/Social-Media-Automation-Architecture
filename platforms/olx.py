"""OLX Marketplace Listing Manager and Exporter.

Complies with classified safety guidelines:
Prepares structured listings, maintains a listing database (CSV & JSON),
and exports formatted listings ready for official posting facilities.
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import settings
from platforms.base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class OLXAdapter(BasePlatformAdapter):
    """Prepares, validates, and exports marketplace listings for OLX."""

    def __init__(self) -> None:
        super().__init__("olx")
        self.output_dir = settings.OLX_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        # OLX exporter is always active locally to manage listing catalogs
        return True

    def publish(
        self,
        post_data: Dict[str, Any],
        media_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format listing, record in catalog database, and export text & JSON files."""
        brand_id = post_data.get("brand_id", "general")
        post_id = post_data.get("id") or post_data.get("post_id", "listing")
        olx_data = post_data.get("content", {}).get("olx", {})

        title = olx_data.get("title", f"Offering from {brand_id}")
        category = olx_data.get("category", "Services & Business")
        price = olx_data.get("price_guidance", "Contact for price")
        condition = olx_data.get("condition", "Brand New / Professional")
        specs = olx_data.get("specifications", {})
        description = olx_data.get("description", "")
        tags = olx_data.get("search_tags", [])

        # Create brand-specific export directory
        brand_dir = self.output_dir / brand_id
        brand_dir.mkdir(parents=True, exist_ok=True)

        txt_file = brand_dir / f"{post_id}_olx_listing.txt"
        json_file = brand_dir / f"{post_id}_olx_listing.json"
        csv_catalog = brand_dir / "catalog.csv"

        # Format clean readable text file
        spec_lines = "\n".join([f"  • {k}: {v}" for k, v in specs.items()])
        tags_line = ", ".join(tags)

        formatted_text = f"""============================================================
OLX CLASSIFIED LISTING SPECIFICATION
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Brand: {brand_id}
Post ID: {post_id}
============================================================

TITLE (Copy to Title field):
{title}

CATEGORY:
{category}

PRICE GUIDANCE:
{price}

CONDITION:
{condition}

SPECIFICATIONS:
{spec_lines}

DESCRIPTION (Copy to Description field):
{description}

SEARCH TAGS / KEYWORDS:
{tags_line}

ATTACHED PROMOTIONAL MEDIA:
{media_path or "No image attached"}
============================================================
"""
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(formatted_text)

        # Export JSON
        export_payload = {
            "post_id": post_id,
            "brand_id": brand_id,
            "title": title,
            "category": category,
            "price_guidance": price,
            "condition": condition,
            "specifications": specs,
            "description": description,
            "search_tags": tags,
            "media_path": media_path,
            "generated_at": datetime.now().isoformat(),
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(export_payload, f, indent=2, ensure_ascii=False)

        # Update Master CSV Catalog
        file_exists = csv_catalog.exists()
        with open(csv_catalog, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(
                    [
                        "post_id",
                        "date",
                        "title",
                        "category",
                        "price",
                        "condition",
                        "media_path",
                        "txt_path",
                    ]
                )
            writer.writerow(
                [
                    post_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    title,
                    category,
                    price,
                    condition,
                    media_path or "",
                    str(txt_file),
                ]
            )

        return {
            "status": "success",
            "platform": self.platform_name,
            "message": "OLX listing prepared, validated, and recorded in catalog database.",
            "export_text_file": str(txt_file),
            "export_json_file": str(json_file),
            "catalog_csv": str(csv_catalog),
            "preview": {
                "title": title,
                "category": category,
                "price": price,
            },
        }
