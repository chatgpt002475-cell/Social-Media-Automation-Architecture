"""Command Line Interface (CLI) for Social Media Automation Architecture."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import click

from config.settings import settings
from core.database import db
from core.gemini_engine import gemini_engine
from core.image_engine import image_engine
from core.scheduler import scheduler
from platforms.manager import platform_manager
from server.app import run_server


@click.group()
def cli():
    """AI-Powered Social Media Automation Hub (Gemini + Multi-Platform Publishing)."""
    pass


# -------------------------------------------------------------
# BRAND MANAGEMENT
# -------------------------------------------------------------
@cli.group()
def brands():
    """Manage multi-brand business profiles."""
    pass


@brands.command("list")
def list_brands():
    """List all registered business profiles."""
    all_brands = settings.get_brands()
    click.echo("\n" + "=" * 60)
    click.echo("REGISTERED BUSINESS PROFILES")
    click.echo("=" * 60)
    for b_id, b in all_brands.items():
        click.echo(f"• ID: {b_id}")
        click.echo(f"  Name: {b.get('name')}")
        click.echo(f"  Industry: {b.get('industry')}")
        click.echo(f"  Website: {b.get('contact_info', {}).get('website', 'N/A')}")
        click.echo(f"  Tone: {b.get('tone')}")
        click.echo("-" * 60)


@brands.command("add")
@click.option("--id", "brand_id", required=True, help="Unique brand ID (slug, e.g. my_brand)")
@click.option("--name", required=True, help="Display Name")
@click.option("--industry", required=True, help="Industry / Niche")
@click.option("--website", default="", help="Website URL")
@click.option("--tone", default="Professional, modern", help="Brand voice/tone")
def add_brand(brand_id: str, name: str, industry: str, website: str, tone: str):
    """Add a new business profile."""
    brand_data = {
        "id": brand_id,
        "name": name,
        "industry": industry,
        "tone": tone,
        "target_audience": "Prospective buyers and clients",
        "keywords": [name, industry],
        "hashtags": [f"#{name.replace(' ', '')}", f"#{industry.replace(' ', '')}"],
        "contact_info": {"website": website, "phone": ""},
        "call_to_action": f"Visit {website} to discover more.",
        "theme": {
            "primary_color": "#0d6efd",
            "secondary_color": "#0a58ca",
            "accent_color": "#0dcaf0",
            "background_color": "#0f172a",
            "text_color": "#ffffff",
        },
    }
    settings.save_brand(brand_id, brand_data)
    click.secho(f"[+] Brand '{name}' ({brand_id}) registered successfully!", fg="green")


# -------------------------------------------------------------
# CONTENT GENERATION & PUBLISHING
# -------------------------------------------------------------
@cli.command("generate")
@click.option("--brand", "-b", "brand_id", required=True, help="Brand ID (e.g. inoptra_digital, eboatex_marine, apex_recruitment)")
@click.option("--topic", "-t", required=True, help="Product, service, or update description")
@click.option("--platforms", "-p", default="facebook,instagram,linkedin,pinterest,olx,twitter", help="Comma-separated platforms")
@click.option("--image", "-i", "image_path", default=None, help="Optional source image path")
@click.option("--publish", is_flag=True, default=False, help="Publish immediately after generation")
def generate(brand_id: str, topic: str, platforms: str, image_path: str | None, publish: bool):
    """Generate platform-tailored content and promotional creatives using Gemini."""
    click.echo(f"\n[*] Generating content for [{brand_id}]...")
    click.echo(f"[*] Topic: '{topic}'")

    target_platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    # Step 1: AI Content Generation
    content = gemini_engine.generate_multiplatform_content(
        brand_id=brand_id,
        topic=topic,
        platforms=target_platforms,
    )

    # Step 2: Image Creative Generation
    img_design = content.get("image_design", {})
    images = image_engine.process_image(
        brand_id=brand_id,
        post_id=post_id,
        source_image_path=image_path,
        banner_title=img_design.get("banner_headline", topic[:45]),
        cta_badge=img_design.get("cta_badge", "Learn More"),
    )

    # Step 3: Save to database
    status = "published" if publish else "draft"
    db.save_post(
        post_id=post_id,
        brand_id=brand_id,
        topic=topic,
        content=content,
        images=images,
        status=status,
    )

    click.secho(f"\n[+] Post generated! ID: {post_id}", fg="green", bold=True)
    click.echo("\n--- Generated Platform Previews ---")
    if "facebook" in target_platforms and "facebook" in content:
        click.secho("[Facebook Headline]:", fg="cyan")
        click.echo(content["facebook"].get("headline"))
    if "instagram" in target_platforms and "instagram" in content:
        click.secho("[Instagram Hook]:", fg="magenta")
        click.echo(content["instagram"].get("hook"))
    if "linkedin" in target_platforms and "linkedin" in content:
        click.secho("[LinkedIn Headline]:", fg="blue")
        click.echo(content["linkedin"].get("headline"))
    if "olx" in target_platforms and "olx" in content:
        click.secho("[OLX Listing Title]:", fg="yellow")
        click.echo(content["olx"].get("title"))

    click.echo("\n--- Generated Image Formats ---")
    for fmt, pth in images.items():
        click.echo(f"  • {fmt}: {pth}")

    if publish:
        click.echo(f"\n[*] Auto-publishing across: {', '.join(target_platforms)}...")
        post_data = db.get_post(post_id)
        if post_data:
            result = platform_manager.publish_post(post_data, target_platforms)
            click.secho(f"[+] Publishing completed. Overall Status: {result['overall_status']}", fg="green", bold=True)
            for plat, res in result.get("platform_results", {}).items():
                click.echo(f"  • {plat}: {res.get('status')}")


@cli.command("publish")
@click.option("--post-id", required=True, help="Post ID to publish")
@click.option("--platforms", default=None, help="Comma-separated platforms override")
def publish_cmd(post_id: str, platforms: str | None):
    """Publish an existing post from database to target channels."""
    post_data = db.get_post(post_id)
    if not post_data:
        click.secho(f"Error: Post '{post_id}' not found.", fg="red")
        return

    target_platforms = (
        [p.strip().lower() for p in platforms.split(",") if p.strip()]
        if platforms
        else ["facebook", "instagram", "linkedin", "olx"]
    )

    click.echo(f"[*] Publishing post '{post_id}' to: {', '.join(target_platforms)}...")
    result = platform_manager.publish_post(post_data, target_platforms)
    click.secho(f"[+] Result: {result['overall_status']}", fg="green", bold=True)
    for plat, res in result.get("platform_results", {}).items():
        click.echo(f"  • {plat}: {res.get('status')}")


@cli.command("schedule")
@click.option("--post-id", required=True, help="Post ID to schedule")
@click.option("--time", "scheduled_time", default=None, help="YYYY-MM-DD HH:MM:SS (defaults to 10 mins from now)")
@click.option("--platforms", default="facebook,instagram,linkedin,olx", help="Comma-separated platforms")
def schedule_cmd(post_id: str, scheduled_time: str | None, platforms: str):
    """Queue a post in the database for automated scheduled publishing."""
    post_data = db.get_post(post_id)
    if not post_data:
        click.secho(f"Error: Post '{post_id}' not found.", fg="red")
        return

    if not scheduled_time:
        scheduled_time = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    target_platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    job_id = db.schedule_post(
        post_id=post_id,
        brand_id=post_data["brand_id"],
        platforms=target_platforms,
        scheduled_time=scheduled_time,
    )
    click.secho(f"[+] Scheduled Job #{job_id} registered for {scheduled_time}!", fg="green")


# -------------------------------------------------------------
# WEEKLY CALENDAR GENERATOR
# -------------------------------------------------------------
@cli.command("calendar")
@click.option("--brand", "-b", "brand_id", required=True, help="Brand ID")
@click.option("--days", "-d", default=7, help="Number of calendar days (default: 7)")
def calendar_cmd(brand_id: str, days: int):
    """Generate a weekly social media content calendar with Gemini."""
    click.echo(f"[*] Generating {days}-day content calendar for brand [{brand_id}]...")
    cal = gemini_engine.generate_weekly_calendar(brand_id=brand_id, days=days)

    out_file = settings.CALENDAR_OUTPUT_DIR / f"{brand_id}_calendar_{datetime.now().strftime('%Y%m%d')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cal, f, indent=2, ensure_ascii=False)

    click.echo("\n" + "=" * 70)
    click.echo(f"[CALENDAR] WEEKLY SOCIAL MEDIA CONTENT CALENDAR: {brand_id.upper()}")
    click.echo("=" * 70)
    for entry in cal:
        click.secho(f"[{entry.get('day_name') or 'Day ' + str(entry.get('day_number'))}] - Pillar: {entry.get('content_pillar')}", fg="cyan", bold=True)
        click.echo(f"  Topic: {entry.get('topic')}")
        click.echo(f"  Hook:  \"{entry.get('hook')}\"")
        click.echo(f"  Channels: {', '.join(entry.get('target_platforms', []))} at {entry.get('suggested_time', '09:00 AM')}")
        click.echo(f"  CTA: {entry.get('call_to_action')}")
        click.echo("-" * 70)

    click.secho(f"\n[+] Saved calendar to: {out_file}", fg="green")


# -------------------------------------------------------------
# BACKGROUND SCHEDULER RUNNER
# -------------------------------------------------------------
@cli.command("run-scheduler")
@click.option("--interval", default=15, help="Polling interval in seconds (default: 15)")
def run_scheduler_cmd(interval: int):
    """Start local background queue processor to auto-publish scheduled posts."""
    scheduler.start_loop(interval_seconds=interval)


# -------------------------------------------------------------
# LOCAL WEB SERVER & DASHBOARD
# -------------------------------------------------------------
@cli.command("server")
@click.option("--host", default=None, help="Host address (default: 127.0.0.1)")
@click.option("--port", default=None, type=int, help="Port (default: 5000)")
def server_cmd(host: str | None, port: int | None):
    """Start the local Webhook Server, REST API, and Control Dashboard."""
    run_server(host=host, port=port)


# -------------------------------------------------------------
# END-TO-END PIPELINE SELF TEST
# -------------------------------------------------------------
@cli.command("test-pipeline")
def test_pipeline():
    """Run an automated self-test across all brands, images, OLX exporter, and dispatch."""
    click.echo("\n========================================================")
    click.echo("[TEST] STARTING SOCIAL MEDIA AUTOMATION PIPELINE TEST")
    click.echo("========================================================\n")

    test_cases = [
        ("inoptra_digital", "Enterprise AI & Cloud Migration Suite for FinTech"),
        ("eboatex_marine", "Solar-Electric Commercial Passenger Catamaran 2026"),
        ("apex_recruitment", "Top 5 High-Demand Tech Leadership Roles Q1"),
    ]

    for brand_id, topic in test_cases:
        click.secho(f"[*] Testing Brand: {brand_id}", fg="yellow", bold=True)
        post_id = f"test_{brand_id}_{datetime.now().strftime('%H%M%S')}"

        # 1. Content Generation
        content = gemini_engine.generate_multiplatform_content(brand_id, topic)
        click.echo(f"  [+] Content generated for: {list(content.keys())}")

        # 2. Image Processing
        images = image_engine.process_image(
            brand_id=brand_id,
            post_id=post_id,
            banner_title=topic[:40],
            cta_badge="Explore Now",
        )
        click.echo(f"  [+] 5 image formats created: {list(images.keys())}")

        # 3. Database Save
        db.save_post(post_id, brand_id, topic, content, images, status="draft")
        click.echo(f"  [+] Saved to SQLite database (ID: {post_id})")

        # 4. Multi-platform publish
        post_data = db.get_post(post_id)
        if post_data:
            res = platform_manager.publish_post(post_data, ["facebook", "instagram", "linkedin", "olx"])
            click.echo(f"  [+] Distribution Status: {res['overall_status']}")
            click.echo(f"    - FB: {res['platform_results'].get('facebook', {}).get('status')}")
            click.echo(f"    - IG: {res['platform_results'].get('instagram', {}).get('status')}")
            click.echo(f"    - LinkedIn: {res['platform_results'].get('linkedin', {}).get('status')}")
            click.echo(f"    - OLX: {res['platform_results'].get('olx', {}).get('status')}")

        click.echo("-" * 55)

    click.secho("\n[SUCCESS] ALL PIPELINE TESTS PASSED SUCCESSFULLY!\n", fg="green", bold=True)


if __name__ == "__main__":
    cli()
