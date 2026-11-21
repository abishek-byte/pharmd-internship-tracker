import os
import re
import feedparser
import requests
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

# ============================================================
# CONFIG — Notion credentials (set via GitHub Secrets)
# ============================================================
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_date: Optional[datetime] = None
    description: str = ""

    def dedupe_key(self) -> str:
        return f"{self.title.lower()}|{self.company.lower()}|{self.location.lower()}"

# ============================================================
# RSS FEED SOURCES — INDIA FOCUSED
# ============================================================
RSS_FEEDS = [
    # -------- Indeed India --------
    {
        "name": "Indeed India - PharmD Intern",
        "url": "https://in.indeed.com/rss?q=PharmD+internship&l=India",
        "source": "Indeed India",
    },
    {
        "name": "Indeed India - Pharmacy Intern",
        "url": "https://in.indeed.com/rss?q=pharmacy+internship+l=India",
        "source": "Indeed India",
    },
    {
        "name": "Indeed India - Industrial Training Pharmacy",
        "url": "https://in.indeed.com/rss?q=industrial+training+pharmacy+l=India",
        "source": "Indeed India",
    },
    {
        "name": "Indeed India - Pharma Fresher",
        "url": "https://in.indeed.com/rss?q=pharma+fresher+l=India",
        "source": "Indeed India",
    },

    # -------- Naukri.com (RSS available for searches) --------
    # Go to naukri.com → search → bottom "RSS Feed" link
    # Example format: https://www.naukri.com/rss/keyword-pharmd-internship
    {
        "name": "Naukri - PharmD Internship",
        "url": "https://www.naukri.com/rss/keyword-pharmd-internship",
        "source": "Naukri",
    },
    {
        "name": "Naukri - Pharmacy Internship",
        "url": "https://www.naukri.com/rss/keyword-pharmacy-internship",
        "source": "Naukri",
    },
    {
        "name": "Naukri - Pharma Fresher",
        "url": "https://www.naukri.com/rss/keyword-pharma-fresher",
        "source": "Naukri",
    },

    # -------- Major Indian Pharma Companies (check if RSS works) --------
    # Many use Workday/ATS with /rss endpoint
    {
        "name": "Sun Pharma Careers",
        "url": "https://sunpharma.wd1.myworkdayjobs.com/rss",
        "source": "Sun Pharma",
    },
    {
        "name": "Cipla Careers",
        "url": "https://cipla.wd1.myworkdayjobs.com/rss",
        "source": "Cipla",
    },
    {
        "name": "Dr. Reddy's Careers",
        "url": "https://drreddys.wd1.myworkdayjobs.com/rss",
        "source": "Dr. Reddy's",
    },
    {
        "name": "Lupin Careers",
        "url": "https://lupin.wd1.myworkdayjobs.com/rss",
        "source": "Lupin",
    },
    {
        "name": "Zydus Cadila Careers",
        "url": "https://zyduscadila.wd1.myworkdayjobs.com/rss",
        "source": "Zydus",
    },
    {
        "name": "Torrent Pharma Careers",
        "url": "https://torrentpharma.wd1.myworkdayjobs.com/rss",
        "source": "Torrent Pharma",
    },
    {
        "name": "Alkem Labs Careers",
        "url": "https://alkemlabs.wd1.myworkdayjobs.com/rss",
        "source": "Alkem Labs",
    },
    {
        "name": "Glenmark Careers",
        "url": "https://glenmark.wd1.myworkdayjobs.com/rss",
        "source": "Glenmark",
    },
    {
        "name": "Aurobindo Pharma Careers",
        "url": "https://aurobindo.wd1.myworkdayjobs.com/rss",
        "source": "Aurobindo",
    },
    {
        "name": "Biocon Careers",
        "url": "https://biocon.wd1.myworkdayjobs.com/rss",
        "source": "Biocon",
    },

    # -------- CROs / Clinical Research --------
    {
        "name": "IQVIA India Careers",
        "url": "https://iqvia.wd1.myworkdayjobs.com/rss",
        "source": "IQVIA",
    },
    {
        "name": "Parexel India Careers",
        "url": "https://parexel.wd1.myworkdayjobs.com/rss",
        "source": "Parexel",
    },
    {
        "name": "Syneos Health Careers",
        "url": "https://syneoshealth.wd1.myworkdayjobs.com/rss",
        "source": "Syneos Health",
    },

    # -------- Regulatory / Government --------
    # PCI, CDSCO, AICTE — usually no RSS, check manually
]

# ============================================================
# KEYWORDS — PharmD Final Year / Industrial Training Focus
# ============================================================
INCLUDE_KEYWORDS = [
    # Core PharmD terms
    "pharmd", "pharm.d", "pharm d",
    "pharmacy intern", "pharmacy internship",
    "industrial training", "industrial training programme",
    "project work", "dissertation", "thesis",
    "final year", "final yr", "5th year", "sixth year",
    "appe", "ippe", "rotation", "clinical rotation",

    # Functions relevant to PharmD
    "clinical research", "clinical trial", "pharmacovigilance",
    "drug safety", "medical affairs", "medical writing",
    "regulatory affairs", "drug regulatory", "ra ",
    "quality assurance", "quality control", "qa qc",
    "production", "manufacturing", "formulation",
    "r&d", "research development", "analytical",
    "drug information", "medical information",
    "pharmacoeconomics", "pharmacovigilance",
    "hospital pharmacy", "clinical pharmacy",
    "community pharmacy", "ambulatory care",

    # Indian context
    "pci", "pharmacy council", "aicte",
    "fresher", "trainee", "graduate trainee",
    "management trainee", "mt ",
]

EXCLUDE_KEYWORDS = [
    "technician", "tech ", "assistant", "cashier", "driver",
    "warehouse", "delivery", "sales associate", "retail associate",
    "medical representative", "mr ", "field sales",
    "business development", "bdm", "area manager",
    "senior", "lead", "manager", "head", "director",
    "experience", "yrs exp", "years exp",
    "walk-in", "walkin", "urgent",
]

# ============================================================
# HELPERS (unchanged)
# ============================================================
def matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    if any(ex in text_lower for ex in EXCLUDE_KEYWORDS):
        return False
    return any(inc in text_lower for inc in INCLUDE_KEYWORDS)

def parse_date(entry) -> Optional[datetime]:
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        if getattr(entry, field, None):
            try:
                return datetime(*entry[field][:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None

def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ============================================================
# NOTION API (unchanged)
# ============================================================
NOTION_API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def notion_query_existing() -> set:
    existing = set()
    has_more = True
    start_cursor = None
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        resp = requests.post(
            f"{NOTION_API}/databases/{NOTION_DB_ID}/query",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("results", []):
            url_prop = page["properties"].get("URL", {}).get("url")
            if url_prop:
                existing.add(url_prop)
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    return existing

def notion_create_page(job: Job) -> bool:
    date_val = None
    if job.posted_date:
        date_val = {"start": job.posted_date.date().isoformat()}

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": job.title[:2000]}}]},
            "Company": {"rich_text": [{"text": {"content": job.company[:2000]}}]},
            "Location": {"rich_text": [{"text": {"content": job.location[:2000]}}]},
            "URL": {"url": job.url},
            "Source": {"select": {"name": job.source[:100]}},
            "Status": {"select": {"name": "New"}},
            "Posted Date": {"date": date_val} if date_val else {"date": None},
            "Description": {"rich_text": [{"text": {"content": job.description[:2000]}}]},
        },
    }
    resp = requests.post(f"{NOTION_API}/pages", headers=HEADERS, json=payload, timeout=30)
    if resp.status_code == 200:
        print(f"  Added: {job.title} @ {job.company}")
        return True
    else:
        print(f"  Failed: {job.title} — {resp.text}")
        return False

# ============================================================
# MAIN FETCH LOOP (unchanged)
# ============================================================
def fetch_feed(feed_config: dict) -> list[Job]:
    jobs = []
    print(f"Fetching: {feed_config['name']} ({feed_config['url']})")
    feed = feedparser.parse(feed_config["url"])
    if feed.bozo:
        print(f"  Parse warning: {feed.bozo_exception}")

    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        summary = clean_html(getattr(entry, "summary", ""))
        link = getattr(entry, "link", "").strip()

        company = feed_config["source"]
        for pattern in [r"^(.+?)\s*[-–|]\s*.+$", r".+\s+at\s+(.+)$"]:
            m = re.match(pattern, title, re.IGNORECASE)
            if m:
                company = m.group(1).strip()
                break

        location = "India / Not specified"
        loc_patterns = [
            r"\b(Remote|Hybrid|On-site)\b",
            r"\b([A-Z][a-z]+,\s*[A-Z]{2,})\b",  # City, State
            r"\b(Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Pune|Kolkata|Ahmedabad|Gurgaon|Noida)\b",
        ]
        for pat in loc_patterns:
            m = re.search(pat, summary + " " + title)
            if m:
                location = m.group(1)
                break

        if not title or not link:
            continue

        searchable = f"{title} {summary}"
        if not matches_keywords(searchable):
            continue

        jobs.append(Job(
            title=title,
            company=company,
            location=location,
            url=link,
            source=feed_config["source"],
            posted_date=parse_date(entry),
            description=summary[:2000],
        ))

    print(f"  Found {len(jobs)} relevant jobs")
    return jobs

def main():
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("Missing NOTION_TOKEN or NOTION_DB_ID environment variables")
        return

    print("Querying existing jobs from Notion...")
    existing_urls = notion_query_existing()
    print(f"   Found {len(existing_urls)} existing entries")

    all_jobs = []
    for feed in RSS_FEEDS:
        try:
            all_jobs.extend(fetch_feed(feed))
        except Exception as e:
            print(f"  Error fetching {feed['name']}: {e}")

    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = job.dedupe_key()
        if key not in seen and job.url not in existing_urls:
            seen.add(key)
            unique_jobs.append(job)

    print(f"\n{len(unique_jobs)} new jobs to add")
    for job in unique_jobs:
        notion_create_page(job)

    print("\nDone!")

if __name__ == "__main__":
    main()
