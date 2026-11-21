 import os
 import re
 import feedparser
 import requests
 from datetime import datetime, timezone
 from dataclasses import dataclass
 from typing import Optional

 # ============================================================
 # CONFIG — edit these to match your Notion setup
 # ============================================================
 NOTION_TOKEN = os.getenv("NOTION_TOKEN")           # secret_xxx
 NOTION_DB_ID = os.getenv("NOTION_DB_ID")           # 32-char database ID
 # ============================================================

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
         """Unique key for deduplication (title + company + location)."""
         return f"{self.title.lower()}|{self.company.lower()}|{self.location.lower()}"

 # ------------------------------------------------------------------
 # RSS FEED SOURCES — add/remove as needed
 # ------------------------------------------------------------------
 RSS_FEEDS = [
     # Indeed — replace with your search URL → "Get RSS feed" link
     # Example: https://rss.indeed.com/rss?q=PharmD+intern&l=New+York
     {
         "name": "Indeed PharmD Intern",
         "url": "https://rss.indeed.com/rss?q=PharmD+intern&l=United+States",
         "source": "Indeed",
     },
     {
         "name": "Indeed Pharmacy Student",
         "url": "https://rss.indeed.com/rss?q=pharmacy+student+intern&l=United+States",
         "source": "Indeed",
     },
     # LinkedIn — use RSS bridge (see README) or email-to-RSS service
     # {
     #     "name": "LinkedIn Pharmacy Intern",
     #     "url": "https://rss-bridge.example.com/linkedin?keywords=pharmacy%20intern",
     #     "source": "LinkedIn",
     # },
     # ASHP Career Center
     {
         "name": "ASHP Pharmacy Jobs",
         "url": "https://careercenter.ashp.org/rss.cfm?site_id=2010&category_id=0",
         "source": "ASHP",
     },
     # ACCP
     {
         "name": "ACCP Career Center",
         "url": "https://careers.accp.com/rss.cfm",
         "source": "ACCP",
     },
     # Major employer career pages (many expose RSS)
     # CVS Health
     # {
     #     "name": "CVS Health Pharmacy",
     #     "url": "https://jobs.cvshealth.com/rss",
     #     "source": "CVS Health",
     # },
     # Walgreens
     # {
     #     "name": "Walgreens Pharmacy",
     #     "url": "https://jobs.walgreens.com/rss",
     #     "source": "Walgreens",
     # },
 ]

 # ------------------------------------------------------------------
 # KEYWORDS — filter for PharmD-relevant roles
 # ------------------------------------------------------------------
 INCLUDE_KEYWORDS = [
     "pharmd", "pharm.d", "pharmacy intern", "pharmacy student",
     "appe", "ippe", "rotation", "clinical pharmacy", "ambulatory",
     "community pharmacy", "hospital pharmacy", "pharmaceutical",
     "medical affairs", "drug information", "mtm", "medication therapy",
     "pharmacy resident", "pgy1", "pgy2", "fellowship",
 ]
 EXCLUDE_KEYWORDS = [
     "technician", "tech ", "assistant", "cashier", "driver",
     "warehouse", "delivery", "sales associate", "retail associate",
 ]

 # ------------------------------------------------------------------
 # HELPERS
 # ------------------------------------------------------------------
 def matches_keywords(text: str) -> bool:
     text_lower = text.lower()
     if any(ex in text_lower for ex in EXCLUDE_KEYWORDS):
         return False
     return any(inc in text_lower for inc in INCLUDE_KEYWORDS)

 def parse_date(entry) -> Optional[datetime]:
     """Parse various date formats from feedparser."""
     for field in ("published_parsed", "updated_parsed", "created_parsed"):
         if getattr(entry, field, None):
             try:
                 return datetime(*entry[field][:6], tzinfo=timezone.utc)
             except Exception:
                 pass
     return None

 def clean_html(text: str) -> str:
     """Strip HTML tags, normalize whitespace."""
     text = re.sub(r"<[^>]+>", " ", text)
     text = re.sub(r"\s+", " ", text)
     return text.strip()

 # ------------------------------------------------------------------
 # NOTION API
 # ------------------------------------------------------------------
 NOTION_API = "https://api.notion.com/v1"
 HEADERS = {
     "Authorization": f"Bearer {NOTION_TOKEN}",
     "Notion-Version": "2022-06-28",
     "Content-Type": "application/json",
 }

 def notion_query_existing() -> set:
     """Fetch existing job URLs from Notion to avoid duplicates."""
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
     """Create a new page in the Notion database."""
     # Format date for Notion
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

 # ------------------------------------------------------------------
 # MAIN FETCH LOOP
 # ------------------------------------------------------------------
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

         # Extract company from title/summary if possible
         company = feed_config["source"]
         # Common patterns: "Company - Title" or "Title at Company"
         for pattern in [r"^(.+?)\s*[-–|]\s*.+$", r".+\s+at\s+(.+)$"]:
             m = re.match(pattern, title, re.IGNORECASE)
             if m:
                 company = m.group(1).strip()
                 break

         # Location — try to extract from summary or title
         location = "Remote / Not specified"
         loc_patterns = [
             r"\b(Remote|Hybrid|On-site)\b",
             r"\b([A-Z][a-z]+,\s*[A-Z]{2})\b",  # City, ST
             r"\b([A-Z]{2})\b",  # State abbreviation
         ]
         for pat in loc_patterns:
             m = re.search(pat, summary + " " + title)
             if m:
                 location = m.group(1)
                 break

         if not title or not link:
             continue

         # Keyword filter
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

     # Deduplicate
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
