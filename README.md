# 🚀 Social Media Automation Architecture

An enterprise-grade, local, AI-powered social media automation hub powered by **Google Gemini AI**. 

Input a product, service, image, or company update once, and the system automatically generates platform-optimized content, synthesizes branded promotional creatives across all aspect ratios, records structured marketplace specifications for OLX, and publishes or schedules directly across multiple social networks and automation engines.

---

## 🏗️ Architecture Overview

```
                               ┌────────────────────────────────┐
                               │   Single Input / Prompt / API  │
                               │  (Product, Service, or Update) │
                               └────────────────┬───────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │            Google Gemini AI Content Engine          │
                     │  - Brand Persona & Tone Alignment (Multi-Brand)     │
                     │  - High-converting Captions, Hooks & Line Spacing   │
                     │  - Researched Hashtags (Niche, Trending & Brand)    │
                     │  - Carousel Slide Outlines & Reel Scripts           │
                     │  - Structured OLX Classified Specifications & Price │
                     │  - Multi-Language & SEO Keyword Tuning              │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │          Automated Image & Creative Engine          │
                     │  - 1:1 Square (Instagram Feed & Facebook)           │
                     │  - 4:5 Portrait (Instagram Feed)                    │
                     │  - 9:16 Story/Reel (Stories & Vertical Video)       │
                     │  - 16:9 Landscape (LinkedIn & Facebook Link Cards)  │
                     │  - 2:3 Pin (Pinterest)                              │
                     │  - Dynamic Brand Badges, Headings, Footers & Watermarks
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │              Local SQLite Database & Queue          │
                     │  - Multi-Brand Profiles (`brands.json`)             │
                     │  - Posts Archive & Image Registry                   │
                     │  - Background Queue & Scheduled Time Triggers       │
                     │  - Full Audit Log & Dispatch History                │
                     └──────────────────────────┬──────────────────────────┘
                                                │
             ┌──────────────────────────────────┴──────────────────────────────────┐
             │                                                                     │
             ▼                                                                     ▼
┌───────────────────────────┐                                         ┌───────────────────────────┐
│     Direct Social APIs    │                                         │    Automation Engines     │
├───────────────────────────┤                                         ├───────────────────────────┤
│ • Facebook Graph API      │                                         │ • Make.com Webhook        │
│ • Instagram Graph API     │                                         │ • n8n Local / Cloud       │
│ • LinkedIn Posts API      │                                         │ • Zapier Webhook          │
│ • Pinterest API v5        │                                         │ • OLX Master CSV & TXT    │
│ • Twitter / X API v2      │                                         │   Export Database         │
└───────────────────────────┘                                         └───────────────────────────┘
```

---

## 🏢 Multi-Brand Profile Support

The system includes pre-configured profiles for your primary brands and allows adding custom brands seamlessly:

| Brand ID | Brand Name | Industry / Focus | Theme Colors |
| :--- | :--- | :--- | :--- |
| `inoptra_digital` | **INOPTRA DIGITAL** | Digital Transformation, IT Services, Enterprise AI & Cloud Migration | Blue (`#0d6efd`) |
| `eboatex_marine` | **EBOATEX MARINE TECHNOLOGIES** | Electric Boats, Naval Propulsion, Clean Maritime & Eco-Tourism | Teal (`#088395`) |
| `apex_recruitment` | **Apex Recruitment** | Executive Search, Tech Hiring & Corporate Talent Acquisition | Emerald (`#198754`) |
| `custom` | **Any Custom Brand** | Easily added via CLI or config file | Custom |

Each profile maintains its own tone, target audience, primary keywords, contact details, CTA guidelines, and brand colors.

---

## ⚡ Key Features

1. **Local & Autonomous**: Runs 100% locally on your machine with no external SaaS dependency required.
2. **Google Gemini Integration**: Generates platform-tailored copy using `gemini-2.5-flash` with automatic fallback to local template mode if an API key is not yet configured.
3. **Automated Creative Processing**: Automatically generates or resizes images into 5 standard social ratios (`1:1`, `4:5`, `9:16`, `16:9`, `2:3`) with brand-consistent badges and typography.
4. **OLX Classified Engine**:
   - Generates compliant, searchable listing titles and buyer-friendly descriptions.
   - Formats structured specifications and price guidance.
   - Maintains a local catalog database (`outputs/olx/<brand>/catalog.csv`) and one-click copyable `.txt` files.
5. **Background Scheduler**: Autonomous background queue processor to auto-publish scheduled posts at exact timestamps.
6. **Local Web Dashboard & REST API**: Built-in Flask dashboard (`http://127.0.0.1:5000`) for one-click generation, brand overview, queue inspection, and webhook triggers.

---

## 🛠️ Quick Start & Setup

### 1. Requirements
- Python 3.10+ (tested on Python 3.14)
- Pip

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
- `GEMINI_API_KEY`: Get a free key from [Google AI Studio](https://aistudio.google.com/).
- *(Optional)* Social API credentials for Facebook, Instagram, LinkedIn, Pinterest, Twitter, or Make/n8n webhooks. 
*(If credentials are left blank, the system runs safely in mock mode, producing fully-formed payloads and local exports for testing).*

---

## 💻 CLI Commands & Usage

All functions are accessible via `python main.py`:

### 1. Brand Management
```bash
# List all registered business profiles
python main.py brands list

# Add a new custom brand
python main.py brands add --id my_brand --name "My Brand" --industry "E-Commerce" --website "https://mybrand.com"
```

### 2. Generate Content & Creatives
```bash
# Generate for INOPTRA DIGITAL
python main.py generate --brand inoptra_digital --topic "Launch of our new AI Workflow Automation suite"

# Generate for EBOATEX MARINE
python main.py generate --brand eboatex_marine --topic "2026 Solar-Electric Luxury Cruiser with Zero Emissions"

# Generate for Apex Recruitment
python main.py generate --brand apex_recruitment --topic "Top 5 High-Demand Tech Leadership Roles in Q1"

# Generate and publish immediately
python main.py generate --brand inoptra_digital --topic "Cloud Cost Optimization Framework" --publish
```

### 3. Generate a 7-Day Social Media Calendar
```bash
python main.py calendar --brand inoptra_digital --days 7
```
*(Saved to `outputs/calendars/<brand>_calendar_<date>.json`)*

### 4. Schedule a Post
```bash
python main.py schedule --post-id <post_id> --time "2026-11-06 14:00:00" --platforms "facebook,instagram,linkedin,olx"
```

### 5. Run the Background Scheduler
```bash
# Polls every 15 seconds and automatically publishes pending posts
python main.py run-scheduler --interval 15
```

### 6. Start the Local Web Dashboard & Webhook Server
```bash
python main.py server --port 5000
```
Open your browser to: **`http://127.0.0.1:5000`**

### 7. Run Pipeline Self-Test
```bash
python main.py test-pipeline
```

---

## 🌐 Webhook Integration (Make.com / n8n / Zapier)

You can trigger generation and publishing directly from Make.com or n8n:

### Inbound Webhook (Trigger generation from Make / n8n):
- **URL**: `http://127.0.0.1:5000/api/webhook/make`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Payload**:
```json
{
  "brand_id": "inoptra_digital",
  "topic": "Announcing our new automated cloud migration assessment",
  "auto_publish": true
}
```

### Outbound Webhook (System dispatches to Make / n8n):
Add your webhook URL in `.env`:
```env
MAKE_WEBHOOK_URL=https://hook.eu1.make.com/your-unique-hook
N8N_WEBHOOK_URL=http://localhost:5678/webhook/your-unique-hook
```
Whenever a post is published, the complete multi-platform payload is forwarded to your automation engine.

---

## 📁 Project Directory Structure

```
Social-Media-Automation-Architecture/
├── config/
│   ├── brands.json          # Profiles for INOPTRA DIGITAL, EBOATEX, Apex Recruitment, etc.
│   └── settings.py          # Settings, directory manager & env loader
├── core/
│   ├── database.py          # SQLite engine (posts, queue, audit logs)
│   ├── gemini_engine.py     # Google Gemini multi-platform AI generator & weekly calendars
│   ├── image_engine.py      # Automated PIL resizer (1:1, 4:5, 9:16, 16:9, 2:3) & brand overlays
│   └── scheduler.py         # Autonomous background queue processor
├── platforms/
│   ├── base.py              # Base adapter interface
│   ├── meta.py              # Facebook Page & Instagram Graph API
│   ├── linkedin.py          # LinkedIn UGC Post API
│   ├── pinterest.py         # Pinterest API v5
│   ├── twitter.py           # Twitter / X API v2
│   ├── olx.py               # OLX listing spec generator & master CSV catalog
│   ├── webhook_dispatcher.py# Dispatches events to Make.com / n8n
│   └── manager.py           # Multi-platform distribution orchestrator
├── server/
│   └── app.py               # Local Flask Web Dashboard, REST API & Webhooks
├── cli.py                   # Click-powered CLI commands
├── main.py                  # Unified entrypoint
├── outputs/                 # Auto-generated images, OLX listings, and calendars
├── data/                    # Local SQLite database (automation.sqlite3)
├── requirements.txt         # Dependencies
├── .env.example             # Configuration template
└── README.md                # Documentation
```

---

## 🔒 Security & Privacy

- All post drafts, image assets, and database records remain strictly on your local machine (`data/` and `outputs/`).
- API credentials are read securely from local `.env` and excluded from git tracking (`.gitignore`).
