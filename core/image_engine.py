"""Automated Image Resizing, Formatting, and Promotional Creative Engine.

Generates platform-compliant creatives using Pillow:
- 1:1 Square (1080x1080) for Instagram Feed & Facebook
- 4:5 Portrait (1080x1350) for Instagram Feed
- 9:16 Story/Reel (1080x1920) for Stories & Reels
- 16:9 Landscape (1200x628) for LinkedIn & Facebook
- 2:3 Pin (1000x1500) for Pinterest
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from config.settings import settings

logger = logging.getLogger(__name__)

PLATFORM_DIMENSIONS: Dict[str, Tuple[int, int]] = {
    "square": (1080, 1080),  # Instagram / Facebook Feed
    "portrait": (1080, 1350),  # Instagram 4:5
    "story_reel": (1080, 1920),  # Reels / Stories 9:16
    "landscape": (1200, 628),  # LinkedIn / FB Banner
    "pinterest": (1000, 1500),  # Pinterest Pin 2:3
}


class ImageEngine:
    """Processes, resizes, and generates social media promotional creatives."""

    def __init__(self) -> None:
        self.output_dir = settings.IMAGES_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _hex_to_rgb(self, hex_code: str) -> Tuple[int, int, int]:
        """Convert hex string (e.g. #0d6efd) to RGB tuple."""
        clean = hex_code.lstrip("#")
        if len(clean) == 3:
            clean = "".join(c * 2 for c in clean)
        if len(clean) != 6:
            return (15, 23, 42)
        return tuple(int(clean[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

    def _get_font(self, size: int) -> ImageFont.ImageFont:
        """Load default or system TrueType font safely."""
        font_candidates = [
            "arial.ttf",
            "Arial.ttf",
            "segoeui.ttf",
            "Segoe UI.ttf",
            "calibri.ttf",
            "Calibri.ttf",
            "DejaVuSans.ttf",
        ]
        for name in font_candidates:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def process_image(
        self,
        brand_id: str,
        post_id: str,
        source_image_path: Optional[str] = None,
        banner_title: str = "",
        cta_badge: str = "",
    ) -> Dict[str, str]:
        """Generate platform-specific images for the given post."""
        brand = settings.get_brand(brand_id) or {
            "name": brand_id.upper(),
            "theme": {
                "primary_color": "#0d6efd",
                "accent_color": "#0dcaf0",
                "background_color": "#0f172a",
                "text_color": "#ffffff",
            },
            "contact_info": {"website": "example.com"},
        }

        brand_dir = self.output_dir / brand_id
        brand_dir.mkdir(parents=True, exist_ok=True)

        generated_files: Dict[str, str] = {}

        for format_name, (width, height) in PLATFORM_DIMENSIONS.items():
            out_filename = f"{post_id}_{format_name}.jpg"
            out_path = brand_dir / out_filename

            if source_image_path and Path(source_image_path).exists():
                img = self._resize_and_overlay(
                    source_image_path=source_image_path,
                    target_size=(width, height),
                    brand=brand,
                    banner_title=banner_title,
                    cta_badge=cta_badge,
                )
            else:
                img = self._generate_branded_card(
                    target_size=(width, height),
                    brand=brand,
                    banner_title=banner_title,
                    cta_badge=cta_badge,
                )

            # Save JPEG with optimal compression
            img.save(str(out_path), "JPEG", quality=90)
            generated_files[format_name] = f"/outputs/images/{brand_id}/{out_filename}"
            generated_files[f"{format_name}_local_path"] = str(out_path)

        return generated_files

    def _resize_and_overlay(
        self,
        source_image_path: str,
        target_size: Tuple[int, int],
        brand: Dict[str, Any],
        banner_title: str,
        cta_badge: str,
    ) -> Image.Image:
        """Fit source image to target dimensions and overlay brand branding."""
        target_w, target_h = target_size
        src = Image.open(source_image_path).convert("RGB")

        # Center crop to target aspect ratio
        src_w, src_h = src.size
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            # Source is wider: crop sides
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            cropped = src.crop((left, 0, left + new_w, src_h))
        else:
            # Source is taller: crop top/bottom
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            cropped = src.crop((0, top, src_w, top + new_h))

        resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(resized, "RGBA")

        # Overlay semi-transparent bottom banner
        banner_h = int(target_h * 0.16)
        draw.rectangle(
            [0, target_h - banner_h, target_w, target_h],
            fill=(10, 15, 25, 220),
        )

        font_brand = self._get_font(int(target_h * 0.035))
        font_sub = self._get_font(int(target_h * 0.022))

        # Brand Name
        brand_name = brand.get("name", "")
        website = brand.get("contact_info", {}).get("website", "")
        draw.text(
            (40, target_h - banner_h + 20),
            brand_name,
            font=font_brand,
            fill=(255, 255, 255, 255),
        )
        draw.text(
            (40, target_h - banner_h + 65),
            website,
            font=font_sub,
            fill=(200, 220, 255, 240),
        )

        # CTA Badge on the right
        if cta_badge:
            badge_text = cta_badge.upper()
            badge_w = 200
            badge_h = 45
            bx1 = target_w - badge_w - 40
            by1 = target_h - banner_h + 25
            primary_color = self._hex_to_rgb(
                brand.get("theme", {}).get("primary_color", "#0d6efd")
            )
            draw.rounded_rectangle(
                [bx1, by1, bx1 + badge_w, by1 + badge_h],
                radius=10,
                fill=(*primary_color, 255),
            )
            draw.text(
                (bx1 + 25, by1 + 12),
                badge_text,
                font=font_sub,
                fill=(255, 255, 255, 255),
            )

        return resized.convert("RGB")

    def _generate_branded_card(
        self,
        target_size: Tuple[int, int],
        brand: Dict[str, Any],
        banner_title: str,
        cta_badge: str,
    ) -> Image.Image:
        """Generate a sleek, modern promotional banner from brand colors and typography."""
        target_w, target_h = target_size
        theme = brand.get("theme", {})
        bg_rgb = self._hex_to_rgb(theme.get("background_color", "#0f172a"))
        primary_rgb = self._hex_to_rgb(theme.get("primary_color", "#0d6efd"))
        accent_rgb = self._hex_to_rgb(theme.get("accent_color", "#0dcaf0"))

        # Base background
        img = Image.new("RGB", (target_w, target_h), bg_rgb)
        draw = ImageDraw.Draw(img, "RGBA")

        # Decorative geometric/tech accents
        draw.polygon(
            [(0, 0), (target_w, 0), (target_w, int(target_h * 0.18)), (0, int(target_h * 0.28))],
            fill=(*primary_rgb, 40),
        )
        draw.ellipse(
            [
                int(target_w * 0.65),
                int(target_h * 0.60),
                int(target_w * 1.3),
                int(target_h * 1.25),
            ],
            fill=(*primary_rgb, 25),
        )

        # Header Badge: Brand Tag
        font_header = self._get_font(int(target_h * 0.032))
        brand_name = brand.get("name", "ENTERPRISE").upper()
        draw.text(
            (60, int(target_h * 0.08)),
            brand_name,
            font=font_header,
            fill=(*accent_rgb, 255),
        )

        # Accent underline
        draw.line(
            [(60, int(target_h * 0.125)), (260, int(target_h * 0.125))],
            fill=(*accent_rgb, 255),
            width=4,
        )

        # Central Title / Headline
        title_text = banner_title or brand.get("tagline", "Innovating Excellence")
        font_title = self._get_font(int(target_h * 0.052))

        # Word-wrap title
        words = title_text.split()
        lines = []
        curr = []
        chars_per_line = max(18, int(target_w / 40))
        for w in words:
            if sum(len(x) + 1 for x in curr) + len(w) > chars_per_line:
                lines.append(" ".join(curr))
                curr = [w]
            else:
                curr.append(w)
        if curr:
            lines.append(" ".join(curr))

        # Draw lines of text
        start_y = int(target_h * 0.35)
        line_spacing = int(target_h * 0.075)
        for idx, line in enumerate(lines[:4]):
            draw.text(
                (60, start_y + (idx * line_spacing)),
                line,
                font=font_title,
                fill=(255, 255, 255, 255),
            )

        # CTA Button
        cta_text = (cta_badge or "DISCOVER MORE").upper()
        font_cta = self._get_font(int(target_h * 0.026))
        cta_y = start_y + (len(lines[:4]) * line_spacing) + 40
        btn_w = min(target_w - 120, 320)
        btn_h = int(target_h * 0.065)
        draw.rounded_rectangle(
            [60, cta_y, 60 + btn_w, cta_y + btn_h],
            radius=12,
            fill=(*primary_rgb, 255),
        )
        draw.text(
            (85, cta_y + int(btn_h * 0.25)),
            cta_text,
            font=font_cta,
            fill=(255, 255, 255, 255),
        )

        # Bottom Bar: Website & Contact
        footer_y = target_h - int(target_h * 0.10)
        draw.line([(60, footer_y), (target_w - 60, footer_y)], fill=(50, 65, 85, 255), width=1)
        font_footer = self._get_font(int(target_h * 0.022))

        website = brand.get("contact_info", {}).get("website", "www.company.com")
        phone = brand.get("contact_info", {}).get("phone", "")
        footer_text = f"🌐 {website}   |   📞 {phone}" if phone else f"🌐 {website}"
        draw.text(
            (60, footer_y + 20),
            footer_text,
            font=font_footer,
            fill=(180, 195, 215, 255),
        )

        return img.convert("RGB")


image_engine = ImageEngine()
