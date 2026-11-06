"""Google Gemini AI Content Generation Engine.

Produces tailored social media captions, hashtags, OLX listings,
and weekly calendars for multiple business brands.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config.settings import settings

logger = logging.getLogger(__name__)


class GeminiEngine:
    """Manages AI generation across multi-brand profiles using Google Gemini."""

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None

    def _get_client(self):
        """Lazy load and initialize Google GenAI client."""
        if self._client is None and self.api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")

    def generate_multiplatform_content(
        self,
        brand_id: str,
        topic: str,
        input_type: str = "general",
        platforms: Optional[List[str]] = None,
        language: str = "English",
        extra_instructions: str = "",
    ) -> Dict[str, Any]:
        """Generate platform-tailored social media content for a given brand and topic."""
        brand = settings.get_brand(brand_id)
        if not brand:
            raise ValueError(f"Brand '{brand_id}' not found in configuration.")

        if platforms is None:
            platforms = ["facebook", "instagram", "linkedin", "pinterest", "olx", "twitter"]

        if not self.is_configured():
            logger.info(
                "Gemini API key not configured or in test mode. Generating high-quality local mock payload."
            )
            return self._generate_mock_content(brand, topic, platforms, language)

        try:
            client = self._get_client()
            if not client:
                return self._generate_mock_content(brand, topic, platforms, language)

            prompt = self._build_prompt(
                brand=brand,
                topic=topic,
                input_type=input_type,
                platforms=platforms,
                language=language,
                extra_instructions=extra_instructions,
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            text_resp = response.text or ""
            return self._parse_json_response(text_resp, brand, topic, platforms, language)
        except Exception as e:
            logger.warning(
                f"Gemini API call encountered error: {e}. Falling back to structured response generator."
            )
            return self._generate_mock_content(brand, topic, platforms, language)

    def generate_weekly_calendar(
        self,
        brand_id: str,
        days: int = 7,
        focus_areas: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a structured multi-day social media publishing calendar."""
        brand = settings.get_brand(brand_id)
        if not brand:
            raise ValueError(f"Brand '{brand_id}' not found in configuration.")

        if not self.is_configured():
            return self._generate_mock_calendar(brand, days)

        try:
            client = self._get_client()
            if not client:
                return self._generate_mock_calendar(brand, days)

            prompt = f"""
You are a senior social media strategist. Create a high-converting {days}-day social media content calendar for:
Brand: {brand['name']}
Industry: {brand['industry']}
Tone: {brand['tone']}
Target Audience: {brand['target_audience']}
Focus Areas: {", ".join(focus_areas or brand['keywords'])}

Return a strict JSON array of objects, each object containing:
- "day_number": integer (1 to {days})
- "day_name": string (e.g. Day 1: Monday)
- "content_pillar": string (e.g. Thought Leadership, Case Study, Product Highlight, Customer Q&A, Industry Trend)
- "topic": string (compelling specific title)
- "hook": string (opening attention grabber)
- "target_platforms": array of strings (e.g. ["linkedin", "facebook", "instagram"])
- "call_to_action": string
- "suggested_time": string (e.g. "09:00 AM" or "02:00 PM")

Return ONLY pure valid JSON with NO markdown code fencing or backticks.
"""
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            text_resp = response.text or ""
            parsed = self._extract_json(text_resp)
            if isinstance(parsed, list):
                return parsed
            return self._generate_mock_calendar(brand, days)
        except Exception as e:
            logger.warning(f"Calendar generation error: {e}. Using template calendar.")
            return self._generate_mock_calendar(brand, days)

    def _build_prompt(
        self,
        brand: Dict[str, Any],
        topic: str,
        input_type: str,
        platforms: List[str],
        language: str,
        extra_instructions: str,
    ) -> str:
        """Construct the prompt for Gemini."""
        return f"""
You are an elite multi-brand digital marketing director and copywriter.
Generate high-converting, platform-specific social media content for:

BRAND PROFILE:
- Brand Name: {brand['name']}
- Industry: {brand['industry']}
- Brand Tone: {brand['tone']}
- Target Audience: {brand['target_audience']}
- Website: {brand.get('contact_info', {}).get('website', '')}
- Phone/Contact: {brand.get('contact_info', {}).get('phone', '')}
- Standard CTA: {brand.get('call_to_action', '')}
- Default Brand Hashtags: {", ".join(brand.get('hashtags', []))}

TASK:
- Topic / Product / Service Update: "{topic}"
- Input Type: {input_type}
- Language: {language}
- Target Platforms: {", ".join(platforms)}
- Additional Instructions: {extra_instructions or "None"}

INSTRUCTIONS PER PLATFORM:
1. Facebook: Catchy headline, storytelling caption with emojis, structured key benefits with bullet points, link and phone CTA, 5-8 relevant hashtags.
2. Instagram: Strong hook line, engaging caption with clean paragraph spacing, 25-30 researched hashtags (split into niche, industry, and trending), plus a 5-slide carousel or reel script concept.
3. LinkedIn: Professional thought-leadership framing, executive voice, industry insight/problem-solution format, 3 bullet takeaways, engaging conversation question at the end, 3-5 professional hashtags.
4. Pinterest: Search-optimized Pin title (under 100 chars), rich SEO description with keywords (under 500 chars), recommended board name, and outbound URL CTA.
5. OLX / Marketplace: High-intent classified listing format. Include listing title (keyword-rich, specs/model), category suggestion, condition, estimated price guidance, structured bullet specs, full buyer-friendly description, contact instructions, and search tags.
6. Twitter (X): Punchy concise tweet (under 260 chars) with hook, key benefit, and CTA link, plus an optional 2nd tweet thread follow-up.
7. Image Design Concept: Headline text for a promotional banner, subtext, and CTA badge text (e.g. "Learn More", "Order Today", "Apply Now").

OUTPUT FORMAT:
Return ONLY a valid JSON object matching this structure (no markdown formatting, no backticks):
{{
  "topic": "{topic}",
  "brand_id": "{brand['id']}",
  "brand_name": "{brand['name']}",
  "facebook": {{
    "headline": "...",
    "caption": "...",
    "hashtags": ["#tag1", "#tag2"]
  }},
  "instagram": {{
    "hook": "...",
    "caption": "...",
    "hashtags": ["#tag1", "#tag2"],
    "carousel_slides": ["Slide 1 concept", "Slide 2 concept", "Slide 3 concept"],
    "reel_script_idea": "..."
  }},
  "linkedin": {{
    "headline": "...",
    "post_body": "...",
    "key_takeaways": ["Takeaway 1", "Takeaway 2"],
    "hashtags": ["#tag1", "#tag2"]
  }},
  "pinterest": {{
    "title": "...",
    "description": "...",
    "board": "...",
    "call_to_action": "..."
  }},
  "olx": {{
    "title": "...",
    "category": "...",
    "price_guidance": "...",
    "condition": "...",
    "specifications": {{
      "Feature 1": "Value",
      "Feature 2": "Value"
    }},
    "description": "...",
    "search_tags": ["tag1", "tag2"]
  }},
  "twitter": {{
    "tweet": "...",
    "thread_followup": "..."
  }},
  "image_design": {{
    "banner_headline": "...",
    "banner_subtext": "...",
    "cta_badge": "..."
  }}
}}
"""

    def _extract_json(self, text: str) -> Any:
        """Strip markdown fences and parse json."""
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    def _parse_json_response(
        self,
        text_resp: str,
        brand: Dict[str, Any],
        topic: str,
        platforms: List[str],
        language: str,
    ) -> Dict[str, Any]:
        """Attempt to parse Gemini response or fallback."""
        try:
            data = self._extract_json(text_resp)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return self._generate_mock_content(brand, topic, platforms, language)

    def _generate_mock_content(
        self,
        brand: Dict[str, Any],
        topic: str,
        platforms: List[str],
        language: str,
    ) -> Dict[str, Any]:
        """Deterministic, rich local content generation when API key is pending."""
        b_name = brand["name"]
        contact = brand.get("contact_info", {})
        website = contact.get("website", "https://example.com")
        phone = contact.get("phone", "+91-98765-00000")
        hashtags = brand.get("hashtags", [])

        return {
            "topic": topic,
            "brand_id": brand["id"],
            "brand_name": b_name,
            "generated_mode": "local_intelligent_template",
            "facebook": {
                "headline": f"🚀 Exciting Update from {b_name}: {topic}",
                "caption": (
                    f"We are thrilled to share our latest milestone at {b_name}!\n\n"
                    f"📌 Highlight: {topic}\n\n"
                    f"At {b_name}, we are dedicated to setting new benchmarks in {brand['industry']}. "
                    f"Our goal is to deliver unmatched reliability, innovation, and value directly to you.\n\n"
                    f"✨ Why this matters:\n"
                    f"• Engineered for high performance and efficiency\n"
                    f"• Tailored to modern operational demands\n"
                    f"• Backed by full support from our expert team\n\n"
                    f"👉 Learn more or get in touch: {website}\n"
                    f"📞 Contact our team: {phone}"
                ),
                "hashtags": hashtags[:6],
            },
            "instagram": {
                "hook": f"The game-changer you've been waiting for: {topic} 🔥",
                "caption": (
                    f"Innovation never stops at {b_name}. ✨\n\n"
                    f"Here is why {topic} is redefining expectations:\n"
                    f"1️⃣ Designed with cutting-edge engineering\n"
                    f"2️⃣ Seamless integration with your existing workflow\n"
                    f"3️⃣ Proven results from day one\n\n"
                    f"Drop a 'YES' below if you want exclusive insights, or tap the link in our bio! 📲\n\n"
                    f"🔗 {website}"
                ),
                "hashtags": hashtags
                + [
                    "#Innovation",
                    "#BusinessGrowth",
                    "#TopTier",
                    "#IndustryLeaders",
                    "#ScaleUp",
                    "#NextGen",
                ],
                "carousel_slides": [
                    f"Slide 1: What is {topic}?",
                    "Slide 2: The Core Problem It Solves",
                    "Slide 3: Key Features & Capabilities",
                    "Slide 4: Real-World Business Impact",
                    f"Slide 5: How To Get Started With {b_name}",
                ],
                "reel_script_idea": (
                    f"Hook (0-3s): 'Stop doing this the hard way.' "
                    f"Body (3-12s): Show problem vs solution with {topic}. "
                    f"CTA (12-15s): 'Check link in bio to learn how {b_name} transforms your results.'"
                ),
            },
            "linkedin": {
                "headline": f"Driving Innovation in {brand['industry']}: {topic}",
                "post_body": (
                    f"In today's fast-moving market, staying ahead requires relentless focus and superior execution.\n\n"
                    f"At {b_name}, we are proud to introduce our latest advancement: {topic}.\n\n"
                    f"Here are 3 critical lessons we learned while engineering this:\n"
                    f"1. Simplicity scales better than complexity.\n"
                    f"2. Measurable business outcomes must always lead technology choices.\n"
                    f"3. Sustainable quality builds enduring customer trust.\n\n"
                    f"{brand['call_to_action']}\n\n"
                    f"What has been your experience addressing this in your organization? Let's discuss in the comments."
                ),
                "key_takeaways": [
                    "Engineered specifically for enterprise scale and reliability.",
                    "Focuses on measurable efficiency gains from day one.",
                    "Directly addresses key bottlenecks in modern operations.",
                ],
                "hashtags": hashtags[:5],
            },
            "pinterest": {
                "title": f"{topic} | {b_name}",
                "description": (
                    f"Discover how {b_name} brings you {topic}. Explore actionable solutions, "
                    f"expert tips, and modern innovations in {brand['industry']}. Click to read more!"
                ),
                "board": f"{b_name} - Solutions & Insights",
                "call_to_action": f"Visit {website} to explore the full guide.",
            },
            "olx": {
                "title": f"{topic} - Premium by {b_name}",
                "category": f"Business & Services / {brand['industry']}",
                "price_guidance": "Contact for pricing / competitive quotes available",
                "condition": "Brand New / Professional Service",
                "specifications": {
                    "Brand / Provider": b_name,
                    "Service Type": topic,
                    "Industry": brand["industry"],
                    "Location Support": contact.get("location", "Pan-India"),
                    "Warranty / Support": "Comprehensive support & consultation",
                },
                "description": (
                    f"Official listing from {b_name}.\n\n"
                    f"Product / Service: {topic}\n"
                    f"Provider: {b_name}\n\n"
                    f"Key Features & Inclusions:\n"
                    f"- High quality, certified enterprise standards\n"
                    f"- On-time delivery and professional deployment\n"
                    f"- Dedicated account specialist and technical support\n\n"
                    f"Contact directly for quotation, brochure, and immediate availability:\n"
                    f"Phone/WhatsApp: {phone}\n"
                    f"Official Website: {website}"
                ),
                "search_tags": [
                    topic.lower(),
                    b_name.lower(),
                    "premium service",
                    "best price",
                    "official",
                ],
            },
            "twitter": {
                "tweet": (
                    f"Big announcement from {b_name}! 🚀\n\n"
                    f"{topic} is here to redefine how we operate in {brand['industry']}.\n\n"
                    f"Discover the details 👉 {website}\n\n"
                    f"{' '.join(hashtags[:3])}"
                ),
                "thread_followup": (
                    f"Why this matters: We solved the #1 friction point our clients face every week. "
                    f"Reply or DM to see a live walkthrough."
                ),
            },
            "image_design": {
                "banner_headline": topic[:45],
                "banner_subtext": f"Engineered by {b_name}",
                "cta_badge": "Explore Now",
            },
        }

    def _generate_mock_calendar(
        self, brand: Dict[str, Any], days: int
    ) -> List[Dict[str, Any]]:
        """Fallback multi-day social media publishing schedule."""
        b_name = brand["name"]
        keywords = brand.get("keywords", ["Innovation", "Efficiency", "Growth"])
        themes = [
            ("Thought Leadership", "Why Traditional Approaches Are Costing You Money", "linkedin"),
            ("Product Highlight", f"Deep Dive into {b_name}'s Flagship Capabilities", "instagram"),
            ("Case Study / Proof", "How Our Clients Cut Operational Overhead by 40%", "linkedin"),
            ("Educational How-To", "3 Common Pitfalls to Avoid in This Space", "facebook"),
            ("Classified Listing", f"Featured Offering on OLX Marketplace", "olx"),
            ("Behind the Scenes", "A Look into Our Engineering & Quality Standard", "instagram"),
            ("Weekly Roundup / AMA", "Ask Us Anything: Direct Founder Q&A Session", "twitter"),
        ]

        calendar = []
        for i in range(days):
            theme_idx = i % len(themes)
            pillar, topic_template, default_plat = themes[theme_idx]
            calendar.append(
                {
                    "day_number": i + 1,
                    "day_name": f"Day {i + 1}",
                    "content_pillar": pillar,
                    "topic": topic_template,
                    "hook": f"Stop scrolling if you want to elevate your {keywords[i % len(keywords)]}.",
                    "target_platforms": [default_plat, "facebook"],
                    "call_to_action": brand.get("call_to_action", "Visit our site to learn more."),
                    "suggested_time": "09:00 AM" if i % 2 == 0 else "02:30 PM",
                }
            )
        return calendar


gemini_engine = GeminiEngine()
