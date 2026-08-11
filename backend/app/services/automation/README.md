# Automation Engine

uDev's knowledge ingestion and enrichment pipeline. Runs on the **OpenRouter free tier** (no paid API).

## Quick Start

```bash
# 1. Install dependencies
cd ~/Code/uDev/automation
pip install -r requirements.txt

# 2. Configure (edit config.yaml)
#    - Set openrouter_api_key if using OpenRouter
#    - Verify browserui_endpoint points to your BrowserUI server
#    - Verify knowledge_root points to ~/Code/uDev/global-knowledge

# 3. Dry-run (preview only)
python engine.py --dry-run

# 4. Run full pipeline
python engine.py

# 5. Process a single topic
python engine.py --topic binder
```

## Pipeline Stages

| Step | Action | Description |
|------|--------|-------------|
| 1 | **Scan** | Walk `global-knowledge/` for `.md` files |
| 2 | **Parse** | Extract front‑matter metadata |
| 3 | **Scrape** | Fetch web references via BrowserUI |
| 4 | **Citations** | Insert footnote references into markdown |
| 5 | **Index** | Update `SUMMARY.md` table of contents |
| 6 | **Notebook** | Convert markdown to `.ipynb` |
| 7 | **Dedup** | SHA256 cache to skip unchanged files |
| 8 | **Git** | Commit & push to `automation/updates` branch |

## Configuration

Edit `config.yaml`:

```yaml
knowledge_root: "~/Code/uDev/global-knowledge"
browserui_endpoint: "http://localhost:8000"
openrouter_api_key: ""   # optional, for enriched scraping

git:
  branch: "automation/updates"
  base_branch: "main"

scraping:
  max_references_per_article: 5
  timeout_seconds: 30
  max_retries: 3
```

## File Structure

```
automation/
├── engine.py          # Main orchestration script
├── config.yaml        # Settings
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Duplicate content | SHA256-based deduplication cache |
| BrowserUI rate limits | Exponential backoff, respects robots.txt |
| Citation errors | URL validation, requests.head pre-check |
| Notebook conversion errors | Fallback to simple cell conversion |
| Unintended commits | Runs on separate `automation/updates` branch |
