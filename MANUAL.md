# 📖 Operator's Manual: Local Social Media Automation Hub
**Run your multi-brand AI publishing workflows with maximum efficiency.**

---

## 🎯 Quick Reference Cheat Sheet

| Task | Recommended Command / Action | Output Location |
| :--- | :--- | :--- |
| **Launch Web Dashboard** | Double-click `start_local_hosting.bat` | Opens browser to `http://localhost:5000` |
| **Instant Single Post (CLI)** | `python main.py generate -b eboatex_marine -t "<Topic>"` | `outputs/images/`, `outputs/olx/`, SQLite |
| **Generate & Auto-Publish** | `python main.py generate -b apex_recruitment -t "<Topic>" --publish` | Published via platform adapters |
| **7-Day Social Calendar** | `python main.py calendar -b eboatex_marine --days 7` | `outputs/calendars/` |
| **Queue a Scheduled Post** | `python main.py schedule --post-id <id> --time "YYYY-MM-DD HH:MM:SS"` | SQLite Queue |
| **Start Background Scheduler**| `python main.py run-scheduler --interval 15` | Background Worker |
| **Self-Test Pipeline** | `python main.py test-pipeline` | Terminal summary |

---

## ⚡ The 3 Operating Modes

### Mode 1: Visual Interactive Dashboard (Best for Daily Review & 1-Click Copy)
1. Double-click [`start_local_hosting.bat`](start_local_hosting.bat) (or run `python main.py server`).
2. Open **[http://localhost:5000](http://localhost:5000)** in your browser.
3. Select your brand (`eboatex_marine`, `apex_recruitment`, or custom).
4. Enter your update, topic, or product details.
5. Select target channels (Facebook, Instagram, LinkedIn, OLX, Pinterest, Twitter).
6. Click **Generate & Distribute**.
7. In the **"View & Copy"** modal:
   - Preview and download any of the 5 generated image sizes.
   - Click **"Copy"** next to any platform to paste directly into your app.
   - Click **"Publish Across Channels"** to trigger direct API dispatch.

---

### Mode 2: High-Speed CLI (Best for Power Users & Scripts)
Generate platform copy and all 5 branded creatives in under 3 seconds:

```bash
# Example 1: EBOATEX MARINE
python main.py generate --brand eboatex_marine --topic "Launch of our 2026 Solar-Electric Luxury Cruiser"

# Example 2: Apex Recruitment
python main.py generate --brand apex_recruitment --topic "Top 5 High-Demand Tech Leadership Roles in Q1"

# Example 3: Publish immediately
python main.py generate --brand eboatex_marine --topic "Zero-emission commercial passenger catamaran" --publish
```

---

### Mode 3: Autonomous Webhook & Scheduler (Set & Forget)
Connect your local system with **Make.com**, **n8n**, or **Zapier**:

1. **Trigger from Make.com or n8n**:
   - Send a `POST` request to: `http://localhost:5000/api/webhook/make`
   - JSON Body:
     ```json
     {
       "brand_id": "eboatex_marine",
       "topic": "Daily inventory update: 24ft Electric Pontoon ready for delivery",
       "auto_publish": true
     }
     ```
2. **Auto-Publish Scheduled Queue**:
   - Keep the scheduler running in a terminal or background task:
     ```bash
     python main.py run-scheduler --interval 30
     ```
   - Any posts queued for the current timestamp will automatically publish without human intervention.

---

## 📅 The 10-Minute Weekly Batch Strategy

To operate with peak efficiency, prepare your entire week in one 10-minute session:

### Step 1: Generate the Weekly Plan
```bash
python main.py calendar --brand eboatex_marine --days 7
```
This generates a 7-day multi-channel roadmap in `outputs/calendars/` with hooks, topics, content pillars, and optimal posting times.

### Step 2: Batch Generate the Posts
Take each topic from the calendar and run:
```bash
python main.py generate --brand eboatex_marine --topic "<Day 1 Topic>"
python main.py generate --brand eboatex_marine --topic "<Day 2 Topic>"
# ... repeat for the week
```

### Step 3: Queue with Exact Times
```bash
python main.py schedule --post-id <post_id_1> --time "2026-11-08 09:00:00"
python main.py schedule --post-id <post_id_2> --time "2026-11-09 14:00:00"
```

### Step 4: Let the Scheduler Run
```bash
python main.py run-scheduler
```
Your local system will automatically publish every post at its appointed time.

---

## 🛒 Handling OLX Classified Listings

OLX requires high-intent specifications and clean formatting:
1. Every time you generate content with `olx` selected, the system creates:
   - `outputs/olx/<brand>/<post_id>_olx_listing.txt` — Pre-formatted fields ready to copy-paste.
   - `outputs/olx/<brand>/<post_id>_olx_listing.json` — Structured specifications.
   - `outputs/olx/<brand>/catalog.csv` — Continuous listing database tracking every item, price, date, and image path.
2. Open the `.txt` file or the Dashboard OLX tab to copy title, price guidance, specifications bullet points, and description directly into the OLX listing form.

---

## 🎨 Image Aspect Ratio Guide

The image engine automatically generates 5 standard social media crops for every post:

| Ratio | Format | Dimensions | Best For |
| :--- | :--- | :--- | :--- |
| **1:1** | Square | 1080 x 1080 px | Instagram Feed, Facebook Post |
| **4:5** | Portrait | 1080 x 1350 px | Instagram Feed (Maximum screen real estate) |
| **9:16**| Story / Reel | 1080 x 1920 px | Instagram Reels, Stories, TikTok |
| **16:9**| Landscape | 1200 x 628 px | LinkedIn Feed, Facebook Link Banners |
| **2:3** | Pin | 1000 x 1500 px | Pinterest Pins |

All images are saved in `outputs/images/<brand_id>/` with your brand colors, watermark, headline banner, and CTA button.

---

## 🏢 Adding a New Business / Brand

To add a new business to your system:

### Option A: Using the CLI
```bash
python main.py brands add \
  --id "my_tech_brand" \
  --name "My Tech Brand" \
  --industry "SaaS & Cloud Computing" \
  --website "https://mytechbrand.com" \
  --tone "Bold, visionary, authoritative"
```

### Option B: Editing `config/brands.json`
Add your brand object to `config/brands.json` specifying your keywords, target audience, brand colors, phone number, and standard CTA.

---

## 🔑 Activating Google Gemini API

By default, if no API key is provided, the system runs in **Intelligent Template Fallback Mode** so everything works immediately. To unlock full AI-written generation:

1. Visit [Google AI Studio](https://aistudio.google.com/) and create a free Gemini API key.
2. Open `.env` in the root folder and add your key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_real_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. Restart your server or CLI. The dashboard badge will change from *Local Intelligent Fallback* to **Gemini: Active**.

---

## 🛠️ Troubleshooting & Maintenance

- **Port Conflict (`WinError 10048`)**: The server automatically detects busy ports and moves to `5001`, `5002`, etc. You can also specify any port manually: `python main.py server --port 5050`.
- **Database Location**: All post records and logs are stored in `data/automation.sqlite3`. Back up this file to preserve post history.
- **Clearing Old Images**: Generated image files live in `outputs/images/`. You can safely archive or delete older subfolders anytime; the database stores their historical metadata.
