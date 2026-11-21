 # PharmD Internship Tracker — Automated Job Search

 A lightweight, free system to automatically fetch PharmD-relevant internship postings from multiple sources into a Notion dashboard.

 ## 🎯 What It Does

 - **Fetches daily** from RSS feeds (Indeed, ASHP, ACCP, company career pages)
   - Filters for PharmD-relevant roles (intern, APPE, IPPE, resident, fellow, clinical, industry)
   - Excludes technician/assistant/cashier roles
 - **Deduplicates** against existing Notion entries (by URL + title+company+location)
 - **Syncs to Notion** with structured fields: Title, Company, Location, Source, Status, Posted Date, Description
 - **Runs free** on GitHub Actions (2,000 min/mo) — no server needed

 ## 📋 Quick Start (15 min)

 ### 1. Fork / Clone This Repo
 ```bash
 git clone https://github.com/YOUR_USERNAME/pharmd-internship-tracker
 cd pharmd-internship-tracker
 ```

 ### 2. Set Up Notion Database
 Follow **[NOTION_SETUP.md](NOTION_SETUP.md)** — creates the database, integration, and connects them.

 ### 3. Add GitHub Secrets
 Repo → Settings → Secrets → Actions → Add:
 - `NOTION_TOKEN` = your `secret_xxx` integration token
 - `NOTION_DB_ID` = 32-char database ID from Notion URL

 ### 4. Customize Feeds (Optional)
 Edit `RSS_FEEDS` in `fetch_jobs.py`:
 - Add your city to Indeed searches
 - Add target company career page RSS feeds
 - Add Handshake/university feeds if available

 ### 5. Test Run
 **GitHub Actions** → **Fetch PharmD Internships** → **Run workflow**
 Check Notion — new jobs appear with Status = "New"

 ### 6. Enable Daily Automation
 Workflow runs daily at 8:00 AM UTC (edit cron in `.github/workflows/fetch-jobs.yml` for your timezone).

 ## 📊 Notion Dashboard

 Once synced, create views:
 - **Kanban by Status** — drag: New → Applied → Interviewing → Offer
 - **Calendar by Deadline** — never miss a due date
 - **Group by Source** — track which channels deliver
 - **Filter: Status = "New"** — your daily review list

 ## 🔧 Configuration

 | File | Purpose |
 |------|---------|
 | `fetch_jobs.py` | Main script — RSS sources, keywords, Notion sync |
 | `requirements.txt` | Python deps (feedparser, requests) |
 | `.github/workflows/fetch-jobs.yml` | Daily schedule (cron) |
 | `NOTION_SETUP.md` | Step-by-step Notion + GitHub setup |

 ### Key Customization Points in `fetch_jobs.py`

 ```python
 # Add your city/state to Indeed searches
 RSS_FEEDS = [
     {"name": "Indeed PharmD Intern - NYC",
      "url": "https://rss.indeed.com/rss?q=PharmD+intern&l=New+York,NY",
      "source": "Indeed"},
 ]

 # Tune keywords for your specialty interests
 INCLUDE_KEYWORDS = ["pharmd", "appe", "clinical pharmacy", "oncology", ...]
 EXCLUDE_KEYWORDS = ["technician", "assistant", "cashier", ...]
 ```

 ## 📈 Sources Included by Default

 | Source | Feed | Notes |
 |--------|------|-------|
 | Indeed | `rss.indeed.com` | Customize query + location |
 | ASHP Career Center | `careercenter.ashp.org/rss` | Hospital/health-system focused |
 | ACCP Career Center | `careers.accp.com/rss` | Clinical/academic focused |
 | *Your additions* | Company career pages | CVS, Walgreens, PBMs, pharma |

 > **LinkedIn**: No public RSS. Use [RSS-Bridge](https://github.com/RSS-Bridge/rss-bridge) self-hosted, or forward email alerts via [Kill the Newsletter](https://kill-the-newsletter.com/) → add as RSS feed.

 ## 🛠 Local Development

 ```bash
 python -m venv .venv
 source .venv/bin/activate  # Windows: .venv\Scripts\activate
 pip install -r requirements.txt

 # Create .env with your credentials
 echo "NOTION_TOKEN=secret_xxx" > .env
 echo "NOTION_DB_ID=your_32_char_id" >> .env

 python fetch_jobs.py
 ```

 ## 💡 Pro Tips for PharmD Students

 - **Timing**: Hospital summer internships post **Oct–Jan**; Pharma rotational programs **Aug–Nov**
 - **Sources to add**: State pharmacy association job boards, PBM career sites (Express Scripts, Optum, Prime), FDA/CDC fellowships
 - **Keywords to add**: Your therapeutic interests (oncology, ID, critical care, ambulatory, pharmacogenomics)
 - **Weekly ritual**: 15 min Monday — review "New" jobs in Notion → apply to top 3–5 → update Status

 ## 📄 License

 MIT — free to use, modify, share.
