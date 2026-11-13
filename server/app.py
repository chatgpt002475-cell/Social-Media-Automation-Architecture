"""Local Webhook Server, REST API, and Interactive Control Dashboard."""
from __future__ import annotations

import json
import logging
import socket
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from flask import Flask, jsonify, render_template_string, request, send_from_directory

from config.settings import settings
from core.database import db
from core.gemini_engine import gemini_engine
from core.image_engine import image_engine
from platforms.manager import platform_manager

# Ensure UTF-8 output encoding across Windows shells
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY

# Serve static output files (generated images, OLX listings, calendars)
@app.route("/outputs/<path:filename>")
def serve_outputs(filename: str):
    """Serve generated image assets and files."""
    return send_from_directory(str(settings.OUTPUTS_DIR), filename)


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
        .brand-badge-eboatex_marine { background-color: #0891b2; color: #fff; }
        .brand-badge-apex_recruitment { background-color: #16a34a; color: #fff; }
        .nav-tabs .nav-link {
            color: var(--text-muted);
            border: none;
            border-bottom: 2px solid transparent;
        }
        .nav-tabs .nav-link.active {
            background: transparent;
            color: var(--accent);
            border-color: var(--accent);
            font-weight: 600;
        }
        .preview-box {
            background-color: #0b1120;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 15px;
            white-space: pre-wrap;
            font-family: inherit;
            font-size: 0.9rem;
            max-height: 380px;
            overflow-y: auto;
        }
        .img-thumb-preview {
            border-radius: 8px;
            border: 1px solid var(--card-border);
            transition: transform 0.2s;
            cursor: pointer;
            width: 100%;
            height: 180px;
            object-fit: cover;
        }
        .img-thumb-preview:hover {
            transform: scale(1.03);
            border-color: var(--accent);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg px-4 mb-4">
        <div class="container-fluid">
            <span class="navbar-brand text-white fw-bold d-flex align-items-center gap-2">
                <i class="bi bi-robot text-info fs-4"></i> Social Media Automation Hub
            </span>
            <div class="d-flex align-items-center gap-3">
                <span class="badge bg-dark border border-secondary text-light px-3 py-2">
                    <i class="bi bi-cpu text-warning me-1"></i> Gemini: {{ 'Active' if gemini_active else 'Local Intelligent Fallback' }}
                </span>
                <span class="badge bg-dark border border-secondary text-light px-3 py-2">
                    <i class="bi bi-hdd-network text-info me-1"></i> Running on Port: {{ port }}
                </span>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4">
        <!-- Stats Row -->
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
                            <div class="text-muted small">TOTAL DISPATCHES</div>
                            <div class="fs-3 fw-bold text-info">{{ stats.successful_publishes }}</div>
                        </div>
                        <i class="bi bi-broadcast text-info fs-1"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="row g-4">
            <!-- Left: Generator Form -->
            <div class="col-lg-5">
                <div class="card p-4 h-100">
                    <h5 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <i class="bi bi-stars text-warning"></i> AI Multi-Platform Generator
                    </h5>
                    <form id="genForm">
                        <div class="mb-3">
                            <label class="form-label text-light fw-semibold small">SELECT BRAND PROFILE</label>
                            <select class="form-select" id="brandSelect" required>
                                {% for b_id, b in brands.items() %}
                                <option value="{{ b_id }}">{{ b.name }} ({{ b.industry }})</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-light fw-semibold small">PRODUCT, SERVICE, OR CONTENT UPDATE TOPIC</label>
                            <textarea class="form-control" id="topicInput" rows="3" placeholder="e.g. Introducing our 2026 Solar-Electric Luxury Passenger Vessel with zero carbon emissions" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-light fw-semibold small">WRITING STYLE / CASING</label>
                            <select class="form-select" id="casingSelect">
                                <option value="standard">Standard Professional (Capitalized)</option>
                                <option value="small_letters">small letters (casual aesthetic / all lowercase)</option>
                                <option value="punchy">Punchy & Bold (Promotional Hook)</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label text-light fw-semibold small">TARGET PLATFORMS</label>
                            <div class="d-flex flex-wrap gap-2">
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="facebook" checked> Facebook</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="instagram" checked> Instagram</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="linkedin" checked> LinkedIn</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="pinterest" checked> Pinterest</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="olx" checked> OLX</label>
                                <label class="btn btn-sm btn-outline-secondary text-white"><input type="checkbox" name="plat" value="twitter" checked> Twitter/X</label>
                            </div>
                        </div>
                        <div class="card p-3 mb-3 border-secondary" style="background: #111927;">
                            <div class="form-check form-switch mb-1">
                                <input class="form-check-input" type="checkbox" id="publishNowCheck">
                                <label class="form-check-label text-white fw-bold" for="publishNowCheck">
                                    Auto-publish immediately across selected channels
                                </label>
                            </div>
                            <div class="small mt-1" style="color: #cbd5e1; font-size: 0.8rem; line-height: 1.4;">
                                <i class="bi bi-shield-check text-info me-1"></i>
                                <strong>Account Safety:</strong> Without real API credentials in <code>.env</code>, dispatches run in <strong>Safe Local Mock Mode</strong> so your actual profiles are never touched.
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold" id="submitBtn">
                            <i class="bi bi-lightning-charge me-1"></i> Generate & Distribute
                        </button>
                    </form>
                    <div id="genAlert" class="mt-3" style="display:none;"></div>
                </div>
            </div>

            <!-- Right: Brand Cards & Publishing Channels -->
            <div class="col-lg-7">
                <div class="card p-4 mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="fw-bold m-0 d-flex align-items-center gap-2">
                            <i class="bi bi-briefcase text-primary"></i> Active Business Profiles
                        </h5>
                    </div>
                    <div class="row g-3">
                        {% for b_id, b in brands.items() %}
                        <div class="col-md-6">
                            <div class="p-3 rounded border border-secondary" style="background:#162032;">
                                <div class="badge brand-badge-{{ b_id }} mb-2">{{ b.name }}</div>
                                <div class="small text-muted mb-2">{{ b.industry }}</div>
                                <div class="small text-info text-truncate"><i class="bi bi-globe me-1"></i>{{ b.contact_info.website }}</div>
                                <div class="small text-muted text-truncate"><i class="bi bi-telephone me-1"></i>{{ b.contact_info.phone }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card p-4">
                    <h5 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <i class="bi bi-diagram-3 text-success"></i> Publishing Channels & Adapters
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
                    <i class="bi bi-clock-history text-info"></i> Generated Posts & Catalogs
                </h5>
                <div>
                    <a href="/api/posts" target="_blank" class="btn btn-sm btn-outline-info me-2">Raw Posts JSON</a>
                    <a href="/api/calendar?brand_id=eboatex_marine&days=7" target="_blank" class="btn btn-sm btn-outline-warning">View 7-Day Calendar</a>
                </div>
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
                    <tbody id="postsTableBody">
                        {% for post in recent_posts %}
                        <tr>
                            <td><code>{{ post.id }}</code></td>
                            <td><span class="badge brand-badge-{{ post.brand_id }}">{{ post.brand_id }}</span></td>
                            <td class="text-truncate" style="max-width:300px;">{{ post.topic }}</td>
                            <td>
                                <span class="badge {{ 'bg-success' if post.status == 'published' else ('bg-warning text-dark' if post.status == 'scheduled' else 'bg-secondary') }}">
                                    {{ post.status }}
                                </span>
                            </td>
                            <td class="small text-muted">{{ post.created_at }}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-info me-1" onclick="viewPost('{{ post.id }}')">
                                    <i class="bi bi-eye"></i> View & Copy
                                </button>
                                <button class="btn btn-sm btn-outline-light" onclick="triggerPublish('{{ post.id }}')">
                                    <i class="bi bi-send"></i> Publish
                                </button>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="6" class="text-center text-muted py-4">No posts in database yet. Use the generator above!</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Post Details Modal -->
    <div class="modal fade" id="postModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content bg-dark text-white border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold" id="modalPostTitle">Post Content & Creatives</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <!-- Nav Tabs -->
                    <ul class="nav nav-tabs mb-3" id="postTab" role="tablist">
                        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-fb">Facebook</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-ig">Instagram</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-li">LinkedIn</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-olx">OLX Listing</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-tw">Twitter/X</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-pin">Pinterest</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-img">Promotional Images</button></li>
                    </ul>

                    <!-- Tab Contents -->
                    <div class="tab-content" id="postTabContent">
                        <!-- Facebook -->
                        <div class="tab-pane fade show active" id="tab-fb">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">Facebook Post Copy</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('fbText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="fbText"></div>
                        </div>

                        <!-- Instagram -->
                        <div class="tab-pane fade" id="tab-ig">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">Instagram Caption & Hashtags</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('igText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="igText"></div>
                            <div class="mt-3">
                                <h6 class="text-warning small mb-1">CAROUSEL SLIDES / REEL SCRIPT CONCEPT</h6>
                                <div class="preview-box" id="igSlides"></div>
                            </div>
                        </div>

                        <!-- LinkedIn -->
                        <div class="tab-pane fade" id="tab-li">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">LinkedIn Article / Update</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('liText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="liText"></div>
                        </div>

                        <!-- OLX -->
                        <div class="tab-pane fade" id="tab-olx">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">OLX Classified Specification & Description</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('olxText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="olxText"></div>
                        </div>

                        <!-- Twitter -->
                        <div class="tab-pane fade" id="tab-tw">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">Twitter / X Post & Thread</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('twText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="twText"></div>
                        </div>

                        <!-- Pinterest -->
                        <div class="tab-pane fade" id="tab-pin">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="text-info m-0">Pinterest Pin Details</h6>
                                <button class="btn btn-sm btn-outline-light" onclick="copyText('pinText')"><i class="bi bi-clipboard me-1"></i>Copy</button>
                            </div>
                            <div class="preview-box" id="pinText"></div>
                        </div>

                        <!-- Images -->
                        <div class="tab-pane fade" id="tab-img">
                            <h6 class="text-info mb-3">Auto-Generated Promotional Creatives (5 Aspect Ratios)</h6>
                            <div class="row g-3" id="imagesContainer"></div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-secondary">
                    <span id="modalPostId" class="text-muted small me-auto"></span>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary" id="modalPublishBtn"><i class="bi bi-send me-1"></i>Publish Across Channels</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentPost = null;
        let postModal = null;

        document.addEventListener('DOMContentLoaded', () => {
            postModal = new bootstrap.Modal(document.getElementById('postModal'));
        });

        document.getElementById('genForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const alertBox = document.getElementById('genAlert');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generating Content & Images...';

            const brand_id = document.getElementById('brandSelect').value;
            const topic = document.getElementById('topicInput').value;
            const casing = document.getElementById('casingSelect').value;
            const publish_now = document.getElementById('publishNowCheck').checked;
            const checkboxes = document.querySelectorAll('input[name="plat"]:checked');
            const platforms = Array.from(checkboxes).map(c => c.value);

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({brand_id, topic, platforms, publish_now, casing})
                });
                const data = await res.json();
                if(!res.ok) throw new Error(data.error || 'Server returned an error');

                alertBox.style.display = 'block';
                alertBox.className = 'alert alert-success';
                alertBox.innerHTML = `<strong>Success!</strong> Post ID <code>${data.post_id}</code> generated! Opening preview...`;

                setTimeout(() => {
                    viewPost(data.post_id);
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-lightning-charge me-1"></i> Generate & Distribute';
                }, 1000);
            } catch (err) {
                alertBox.style.display = 'block';
                alertBox.className = 'alert alert-danger';
                alertBox.innerText = 'Error: ' + err.message;
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-lightning-charge me-1"></i> Generate & Distribute';
            }
        });

        async function viewPost(postId) {
            try {
                const res = await fetch(`/api/posts/${postId}`);
                if(!res.ok) throw new Error('Post not found');
                const post = await res.json();
                currentPost = post;

                document.getElementById('modalPostTitle').innerText = `${post.brand_id.toUpperCase()} — ${post.topic}`;
                document.getElementById('modalPostId').innerText = `Post ID: ${post.id}`;

                const c = post.content || {};

                // Facebook
                const fb = c.facebook || {};
                document.getElementById('fbText').innerText = `${fb.headline || ''}\\n\\n${fb.caption || ''}\\n\\n${(fb.hashtags || []).join(' ')}`;

                // Instagram
                const ig = c.instagram || {};
                document.getElementById('igText').innerText = `${ig.hook || ''}\\n\\n${ig.caption || ''}\\n\\n${(ig.hashtags || []).join(' ')}`;
                document.getElementById('igSlides').innerText = `Slides:\\n• ${(ig.carousel_slides || []).join('\\n• ')}\\n\\nReel Idea:\\n${ig.reel_script_idea || 'N/A'}`;

                // LinkedIn
                const li = c.linkedin || {};
                document.getElementById('liText').innerText = `${li.headline || ''}\\n\\n${li.post_body || ''}\\n\\nKey Takeaways:\\n• ${(li.key_takeaways || []).join('\\n• ')}\\n\\n${(li.hashtags || []).join(' ')}`;

                // OLX
                const olx = c.olx || {};
                let specs = '';
                if(olx.specifications) {
                    specs = Object.entries(olx.specifications).map(([k, v]) => `• ${k}: ${v}`).join('\\n');
                }
                document.getElementById('olxText').innerText = `TITLE:\\n${olx.title || ''}\\n\\nCATEGORY: ${olx.category || ''}\\nPRICE: ${olx.price_guidance || ''}\\n\\nSPECIFICATIONS:\\n${specs}\\n\\nDESCRIPTION:\\n${olx.description || ''}`;

                // Twitter
                const tw = c.twitter || {};
                document.getElementById('twText').innerText = `${tw.tweet || ''}\\n\\nFollow-up Thread:\\n${tw.thread_followup || ''}`;

                // Pinterest
                const pin = c.pinterest || {};
                document.getElementById('pinText').innerText = `TITLE: ${pin.title || ''}\\nBOARD: ${pin.board || ''}\\n\\nDESCRIPTION:\\n${pin.description || ''}\\n\\nCTA: ${pin.call_to_action || ''}`;

                // Images
                const imgContainer = document.getElementById('imagesContainer');
                imgContainer.innerHTML = '';
                const imgs = post.images || {};
                for(const [fmt, path] of Object.entries(imgs)) {
                    if(fmt.includes('_local_path')) continue;
                    const col = document.createElement('div');
                    col.className = 'col-md-4';
                    col.innerHTML = `
                        <div class="card p-2 text-center" style="background:#111927;">
                            <div class="small text-muted mb-1 text-uppercase">${fmt}</div>
                            <a href="${path}" target="_blank">
                                <img src="${path}" class="img-thumb-preview mb-2" alt="${fmt}">
                            </a>
                            <a href="${path}" download class="btn btn-xs btn-outline-info w-100">
                                <i class="bi bi-download me-1"></i>Download
                            </a>
                        </div>
                    `;
                    imgContainer.appendChild(col);
                }

                document.getElementById('modalPublishBtn').onclick = () => triggerPublish(post.id);
                postModal.show();
            } catch(e) {
                alert('Failed to load post: ' + e.message);
            }
        }

        async function triggerPublish(postId) {
            if(!confirm(`Publish post ${postId} now?`)) return;
            try {
                const res = await fetch('/api/publish', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({post_id: postId})
                });
                const data = await res.json();
                alert(`Dispatch completed! Status: ${data.overall_status || 'OK'}`);
                window.location.reload();
            } catch(e) {
                alert('Publish failed: ' + e.message);
            }
        }

        function copyText(elemId) {
            const text = document.getElementById(elemId).innerText;
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard!');
            });
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index() -> str:
    """Render the main control dashboard."""
    brands = settings.get_brands()
    recent_posts = db.list_posts(limit=25)
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
    return jsonify({
        "status": "healthy",
        "time": datetime.now().isoformat(),
        "gemini_active": gemini_engine.is_configured(),
        "database": str(settings.DB_PATH.exists()),
    })


@app.route("/api/brands", methods=["GET"])
def get_brands_api() -> Any:
    return jsonify(settings.get_brands())


def normalize_post_payload(post: Dict[str, Any]) -> Dict[str, Any]:
    """Convert local Windows filesystem image paths to browser-accessible /outputs/ URLs."""
    post_copy = dict(post)
    images = dict(post_copy.get("images") or {})
    normalized_imgs = {}
    for fmt, pth in images.items():
        if not isinstance(pth, str):
            continue
        clean = pth.replace("\\", "/")
        if "/outputs/" in clean:
            clean = "/outputs/" + clean.split("/outputs/", 1)[1]
        elif clean.startswith("outputs/"):
            clean = "/" + clean
        normalized_imgs[fmt] = clean
    post_copy["images"] = normalized_imgs
    return post_copy


@app.route("/api/posts", methods=["GET"])
def list_posts_api() -> Any:
    brand_id = request.args.get("brand_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", "50"))
    posts = db.list_posts(brand_id=brand_id, status=status, limit=limit)
    return jsonify([normalize_post_payload(p) for p in posts])


@app.route("/api/posts/<post_id>", methods=["GET"])
def get_post_detail_api(post_id: str) -> Any:
    post = db.get_post(post_id)
    if not post:
        return jsonify({"error": f"Post '{post_id}' not found"}), 404
    return jsonify(normalize_post_payload(post))


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

    casing = payload.get("casing", "standard")
    extra_instructions = ""
    if casing == "small_letters":
        extra_instructions = "Write all captions, hooks, and hashtags strictly in lowercase / small letters (casual aesthetic)."
    elif casing == "punchy":
        extra_instructions = "Write in high-energy, punchy, promotional style."

    # Step 1: AI Content Generation with Gemini
    content = gemini_engine.generate_multiplatform_content(
        brand_id=brand_id,
        topic=topic,
        platforms=platforms,
        language=language,
        extra_instructions=extra_instructions,
    )

    if casing == "small_letters":
        def apply_lowercase(data):
            if isinstance(data, str):
                return data.lower()
            elif isinstance(data, list):
                return [apply_lowercase(x) for x in data]
            elif isinstance(data, dict):
                return {k: apply_lowercase(v) for k, v in data.items()}
            return data
        content = apply_lowercase(content)

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
    topic = payload.get("topic") or payload.get("title") or payload.get("prompt")
    brand_id = payload.get("brand_id", "eboatex_marine")
    auto_publish = payload.get("auto_publish", True)

    if not topic:
        return jsonify({"error": "Topic/title payload required"}), 400

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


def find_available_port(host: str, start_port: int, max_attempts: int = 20) -> int:
    """Find a guaranteed free port to avoid WinError 10048."""
    check_host = "127.0.0.1" if host == "0.0.0.0" else host
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((check_host, p))
                return p
            except OSError:
                continue
    return start_port


def run_server(host: str | None = None, port: int | None = None) -> None:
    """Start local server with automatic port conflict resolution."""
    raw_h = host or settings.SERVER_HOST or "0.0.0.0"
    req_p = port or settings.SERVER_PORT or 5000
    actual_p = find_available_port(raw_h, req_p)

    settings.SERVER_PORT = actual_p

    if actual_p != req_p:
        print(f"[!] Note: Port {req_p} was in use. Automatically switched to free port {actual_p}.")

    print(f"\n========================================================")
    print(f"🚀 Social Media Automation Hub running locally!")
    print(f"👉 Local Web Dashboard: http://localhost:{actual_p}")
    print(f"👉 Direct IPv4 Link:    http://127.0.0.1:{actual_p}")
    print(f"👉 REST API & Webhooks: http://127.0.0.1:{actual_p}/api/generate")
    print(f"========================================================\n")

    app.run(host=raw_h, port=actual_p, debug=False)
