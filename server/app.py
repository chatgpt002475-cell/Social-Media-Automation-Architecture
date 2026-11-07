"""Local Webhook Server, REST API, and Control Dashboard."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import uuid4

from flask import Flask, jsonify, render_template_string, request

from config.settings import settings
from core.database import db
from core.gemini_engine import gemini_engine
from core.image_engine import image_engine
from platforms.manager import platform_manager

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY

# Minimalist, modern dark-mode responsive dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Media Automation Hub</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --accent: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: system-ui, -apple-system, sans-serif;
            padding-bottom: 60px;
        }
        .navbar {
            background-color: var(--card-bg);
            border-bottom: 1px solid var(--card-border);
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            color: var(--text-main);
        }
        .stat-card {
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
        }
        .table {
            color: var(--text-main);
        }
        .table thead th {
            border-bottom: 1px solid var(--card-border);
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        .table td {
            border-top: 1px solid var(--card-border);
            vertical-align: middle;
        }
        .badge-brand {
            background-color: #3b82f6;
            color: white;
            font-weight: 500;
        }
        .platform-pill {
            display: inline-block;
            padding: 2px 8px;
            font-size: 0.75rem;
            border-radius: 12px;
            margin-right: 4px;
            background: #334155;
            color: #e2e8f0;
        }
        .form-control, .form-select {
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            color: #f8fafc;
        }
        .form-control:focus, .form-select:focus {
            background-color: #0f172a;
            border-color: var(--accent);
            color: #f8fafc;
            box-shadow: 0 0 0 0.25rem rgba(56, 189, 248, 0.25);
        }
        .brand-badge-eboatex_marine { background-color: #0891b2; }
        .brand-badge-apex_recruitment { background-color: #16a34a; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg px-4 mb-4">
        <div class="container-fluid">
            <span class="navbar-brand text-white fw-bold d-flex align-items-center gap-2">
                <i class="bi bi-robot text-info fs-4"></i> Social Media Automation Architecture
            </span>
            <div class="d-flex align-items-center gap-3">
                <span class="badge bg-dark border border-secondary text-light px-3 py-2">
                    <i class="bi bi-cpu text-warning me-1"></i> Gemini: {{ 'Active' if gemini_active else 'Demo/Mock Mode' }}
                </span>
                <span class="badge bg-dark border border-secondary text-light px-3 py-2">
                    <i class="bi bi-clock text-info me-1"></i> Local Server: 127.0.0.1:{{ port }}
                </span>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4">
        <!-- Quick Stats Cards -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card stat-card p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small">TOTAL POSTS</div>
                            <div class="fs-3 fw-bold">{{ stats.total_posts }}</div>
                        </div>
                        <i class="bi bi-file-earmark-text text-primary fs-1"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small">PUBLISHED POSTS</div>
                            <div class="fs-3 fw-bold text-success">{{ stats.published_posts }}</div>
                        </div>
                        <i class="bi bi-check-circle text-success fs-1"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small">SCHEDULED QUEUE</div>
                            <div class="fs-3 fw-bold text-warning">{{ stats.pending_queue }}</div>
                        </div>
                        <i class="bi bi-calendar-event text-warning fs-1"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card p-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small">DISPATCH ATTEMPTS</div>
                            <div class="fs-3 fw-bold text-info">{{ stats.successful_publishes }}</div>
                        </div>
                        <i class="bi bi-broadcast text-info fs-1"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="row g-4">
            <!-- Left: Quick Generator Form -->
            <div class="col-lg-5">
                <div class="card p-4 h-100">
                    <h5 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <i class="bi bi-stars text-warning"></i> AI Multi-Platform Generator
                    </h5>
                    <form id="genForm">
                        <div class="mb-3">
                            <label class="form-label text-muted small">SELECT BRAND PROFILE</label>
                            <select class="form-select" id="brandSelect" required>
                                {% for b_id, b in brands.items() %}
                                <option value="{{ b_id }}">{{ b.name }} ({{ b.industry }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted small">PRODUCT, SERVICE, OR UPDATE TOPIC</label>
                            <textarea class="form-control" id="topicInput" rows="3" placeholder="e.g. Launch of our new automated AI workflow suite with instant CRM sync" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-muted small">TARGET PLATFORMS</label>
                            <div class="d-flex flex-wrap gap-2">
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="facebook" checked> Facebook</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="instagram" checked> Instagram</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="linkedin" checked> LinkedIn</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="pinterest" checked> Pinterest</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="olx" checked> OLX</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="twitter" checked> Twitter/X</label>
                            </div>
                        </div>
                        <div class="form-check form-switch mb-3">
                            <input class="form-check-input" type="checkbox" id="publishNowCheck">
                            <label class="form-check-label text-muted small" for="publishNowCheck">Auto-publish immediately across selected platforms</label>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold" id="submitBtn">
                            <i class="bi bi-lightning-charge me-1"></i> Generate & Distribute
                        </button>
                    </form>
                    <div id="genAlert" class="mt-3" style="display:none;"></div>
                </div>
            </div>

            <!-- Right: Configured Brands & Platform Status -->
            <div class="col-lg-7">
                <div class="card p-4 mb-4">
                    <h5 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <i class="bi bi-briefcase text-primary"></i> Active Business Profiles
                    </h5>
                    <div class="row g-3">
                        {% for b_id, b in brands.items() %}
                        <div class="col-md-4">
                            <div class="p-3 rounded border border-secondary" style="background:#162032;">
                                <div class="badge brand-badge-{{ b_id }} mb-2">{{ b.name }}</div>
                                <div class="small text-muted mb-1">{{ b.industry }}</div>
                                <div class="small text-info text-truncate">{{ b.contact_info.website }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card p-4">
                    <h5 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <i class="bi bi-diagram-3 text-success"></i> Publishing Channels & Automation Engines
                    </h5>
                    <div class="d-flex flex-wrap gap-2">
                        {% for p_name, p_status in platform_status.items() %}
                        <span class="badge border border-secondary px-3 py-2 {{ 'bg-success text-white' if p_status else 'bg-dark text-muted' }}">
                            <i class="bi {{ 'bi-check-circle-fill' if p_status else 'bi-dash-circle' }} me-1"></i>
                            {{ p_name.upper() }} ({{ 'Connected' if p_status else 'Mock/Local Ready' }})
                        </span>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Posts Table -->
        <div class="card p-4 mt-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="fw-bold m-0 d-flex align-items-center gap-2">
                    <i class="bi bi-clock-history text-info"></i> Recent Generated Posts & History
                </h5>
                <a href="/api/posts" target="_blank" class="btn btn-sm btn-outline-info">View Raw JSON API</a>
            </div>
            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Post ID</th>
                            <th>Brand</th>
                            <th>Topic</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for post in recent_posts %}
                        <tr>
                            <td><code>{{ post.id }}</code></td>
                            <td><span class="badge brand-badge-{{ post.brand_id }}">{{ post.brand_id }}</span></td>
                            <td class="text-truncate" style="max-width:320px;">{{ post.topic }}</td>
                            <td>
                                <span class="badge {{ 'bg-success' if post.status == 'published' else ('bg-warning text-dark' if post.status == 'scheduled' else 'bg-secondary') }}">
                                    {{ post.status }}
                                </span>
                            </td>
                            <td class="small text-muted">{{ post.created_at }}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-light" onclick="triggerPublish('{{ post.id }}')">
                                    <i class="bi bi-send"></i> Publish
                                </button>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-4">No posts generated yet. Use the generator above or CLI!</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('genForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const alertBox = document.getElementById('genAlert');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing with AI...';

            const brand_id = document.getElementById('brandSelect').value;
            const topic = document.getElementById('topicInput').value;
            const publish_now = document.getElementById('publishNowCheck').checked;
            const checkboxes = document.querySelectorAll('input[name="plat"]:checked');
            const platforms = Array.from(checkboxes).map(c => c.value);

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({brand_id, topic, platforms, publish_now})
                });
                const data = await res.json();
                alertBox.style.display = 'block';
                alertBox.className = 'alert alert-success';
                alertBox.innerHTML = `<strong>Success!</strong> Post ID <code>${data.post_id}</code> generated and processed. Reloading...`;
                setTimeout(() => window.location.reload(), 1500);
            } catch (err) {
                alertBox.style.display = 'block';
                alertBox.className = 'alert alert-danger';
                alertBox.innerText = 'Error: ' + err.message;
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-lightning-charge me-1"></i> Generate & Distribute';
            }
        });

        async function triggerPublish(postId) {
            if(!confirm(`Publish post ${postId} now?`)) return;
            try {
                const res = await fetch('/api/publish', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({post_id: postId})
                });
                const data = await res.json();
                alert(`Published! Status: ${data.overall_status || 'OK'}`);
                window.location.reload();
            } catch(e) {
                alert('Publish failed: ' + e.message);
            }
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index() -> str:
    """Render the main control dashboard."""
    brands = settings.get_brands()
    recent_posts = db.list_posts(limit=15)
    stats = db.get_dashboard_stats()
    platform_status = platform_manager.get_platform_status()
    gemini_active = gemini_engine.is_configured()

    return render_template_string(
        DASHBOARD_HTML,
        brands=brands,
        recent_posts=recent_posts,
        stats=stats,
        platform_status=platform_status,
        gemini_active=gemini_active,
        port=settings.SERVER_PORT,
    )


@app.route("/api/health", methods=["GET"])
def health_check() -> Any:
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})


@app.route("/api/brands", methods=["GET"])
def get_brands_api() -> Any:
    return jsonify(settings.get_brands())


@app.route("/api/posts", methods=["GET"])
def list_posts_api() -> Any:
    brand_id = request.args.get("brand_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", "50"))
    posts = db.list_posts(brand_id=brand_id, status=status, limit=limit)
    return jsonify(posts)


@app.route("/api/calendar", methods=["GET"])
def get_calendar_api() -> Any:
    brand_id = request.args.get("brand_id", "eboatex_marine")
    days = int(request.args.get("days", "7"))
    calendar = gemini_engine.generate_weekly_calendar(brand_id=brand_id, days=days)
    return jsonify({"brand_id": brand_id, "days": days, "calendar": calendar})


@app.route("/api/generate", methods=["POST"])
def generate_api() -> Any:
    """Generate social media post content using Gemini and optionally publish immediately."""
    payload = request.get_json() or {}
    brand_id = payload.get("brand_id", "eboatex_marine")
    topic = payload.get("topic", "")
    platforms = payload.get("platforms")
    publish_now = payload.get("publish_now", False)
    image_path = payload.get("image_path")
    language = payload.get("language", "English")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    post_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    # Step 1: AI Content Generation with Gemini
    content = gemini_engine.generate_multiplatform_content(
        brand_id=brand_id,
        topic=topic,
        platforms=platforms,
        language=language,
    )

    # Step 2: Auto-resize and generate promotional creatives
    img_design = content.get("image_design", {})
    images = image_engine.process_image(
        brand_id=brand_id,
        post_id=post_id,
        source_image_path=image_path,
        banner_title=img_design.get("banner_headline", topic[:45]),
        cta_badge=img_design.get("cta_badge", "Learn More"),
    )

    # Step 3: Save to SQLite database
    initial_status = "published" if publish_now else "draft"
    db.save_post(
        post_id=post_id,
        brand_id=brand_id,
        topic=topic,
        content=content,
        images=images,
        status=initial_status,
    )

    # Step 4: Dispatch immediately if requested
    publish_result = None
    if publish_now:
        post_data = db.get_post(post_id)
        if post_data:
            publish_result = platform_manager.publish_post(
                post_data=post_data,
                target_platforms=platforms,
            )

    return jsonify(
        {
            "post_id": post_id,
            "brand_id": brand_id,
            "topic": topic,
            "status": "published" if publish_now else "draft",
            "content": content,
            "images": images,
            "publish_result": publish_result,
        }
    )


@app.route("/api/publish", methods=["POST"])
def publish_api() -> Any:
    """Publish an existing post by ID."""
    payload = request.get_json() or {}
    post_id = payload.get("post_id")
    platforms = payload.get("platforms")

    if not post_id:
        return jsonify({"error": "post_id is required"}), 400

    post_data = db.get_post(post_id)
    if not post_data:
        return jsonify({"error": f"Post '{post_id}' not found"}), 404

    result = platform_manager.publish_post(post_data=post_data, target_platforms=platforms)
    return jsonify(result)


@app.route("/api/schedule", methods=["POST"])
def schedule_api() -> Any:
    """Schedule a post for future execution."""
    payload = request.get_json() or {}
    post_id = payload.get("post_id")
    platforms = payload.get("platforms") or ["facebook", "instagram", "linkedin", "olx"]
    scheduled_time = payload.get("scheduled_time")

    if not post_id:
        return jsonify({"error": "post_id is required"}), 400

    if not scheduled_time:
        # Default to 10 minutes from now
        scheduled_time = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    post_data = db.get_post(post_id)
    if not post_data:
        return jsonify({"error": f"Post '{post_id}' not found"}), 404

    job_id = db.schedule_post(
        post_id=post_id,
        brand_id=post_data["brand_id"],
        platforms=platforms,
        scheduled_time=scheduled_time,
    )

    return jsonify(
        {
            "job_id": job_id,
            "post_id": post_id,
            "scheduled_time": scheduled_time,
            "platforms": platforms,
            "status": "scheduled",
        }
    )


@app.route("/api/webhook/make", methods=["POST"])
def make_webhook_inbound() -> Any:
    """Inbound webhook receiver for Make.com / n8n triggers."""
    payload = request.get_json() or {}
    logger.info(f"Received inbound webhook: {payload}")

    topic = payload.get("topic") or payload.get("title") or payload.get("prompt")
    brand_id = payload.get("brand_id", "eboatex_marine")
    auto_publish = payload.get("auto_publish", True)

    if not topic:
        return jsonify({"error": "Topic/title payload required"}), 400

    # Auto-generate & distribute
    post_id = f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
    content = gemini_engine.generate_multiplatform_content(brand_id=brand_id, topic=topic)
    images = image_engine.process_image(brand_id=brand_id, post_id=post_id, banner_title=topic[:45])

    db.save_post(
        post_id=post_id,
        brand_id=brand_id,
        topic=topic,
        content=content,
        images=images,
        status="published" if auto_publish else "draft",
    )

    pub_res = None
    if auto_publish:
        post_data = db.get_post(post_id)
        if post_data:
            pub_res = platform_manager.publish_post(post_data=post_data)

    return jsonify(
        {
            "status": "success",
            "post_id": post_id,
            "brand_id": brand_id,
            "publish_result": pub_res,
        }
    )


def run_server(host: str | None = None, port: int | None = None) -> None:
    """Start local server."""
    h = host or settings.SERVER_HOST
    p = port or settings.SERVER_PORT
    print(f"\n========================================================")
    print(f"🚀 Social Media Automation Hub running locally!")
    print(f"👉 Local Web Dashboard: http://{h}:{p}")
    print(f"👉 REST API & Webhooks: http://{h}:{p}/api/generate")
    print(f"========================================================\n")
    app.run(host=h, port=p, debug=False)
