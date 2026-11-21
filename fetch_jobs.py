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
# RSS FEED SOURCES — COMPREHENSIVE INDIA PHARMA
# ============================================================
RSS_FEEDS = [
    # ===== JOB BOARDS =====
    {"name": "Indeed India - PharmD Internship", "url": "https://in.indeed.com/rss?q=PharmD+internship&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Pharmacy Internship", "url": "https://in.indeed.com/rss?q=pharmacy+internship&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Industrial Training Pharmacy", "url": "https://in.indeed.com/rss?q=industrial+training+pharmacy&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Pharma Fresher", "url": "https://in.indeed.com/rss?q=pharma+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Pharmacovigilance Fresher", "url": "https://in.indeed.com/rss?q=pharmacovigilance+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Medical Writing Fresher", "url": "https://in.indeed.com/rss?q=medical+writing+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Regulatory Affairs Fresher", "url": "https://in.indeed.com/rss?q=regulatory+affairs+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Clinical Research Fresher", "url": "https://in.indeed.com/rss?q=clinical+research+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - QA QC Pharma Fresher", "url": "https://in.indeed.com/rss?q=qa+qc+pharma+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Production Pharma Fresher", "url": "https://in.indeed.com/rss?q=production+pharma+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - R&D Pharma Fresher", "url": "https://in.indeed.com/rss?q=r%26d+pharma+fresher&l=India", "source": "Indeed India"},
    {"name": "Indeed India - Drug Safety Fresher", "url": "https://in.indeed.com/rss?q=drug+safety+fresher&l=India", "source": "Indeed India"},

    {"name": "Naukri - PharmD Internship", "url": "https://www.naukri.com/rss/keyword-pharmd-internship", "source": "Naukri"},
    {"name": "Naukri - Pharmacy Internship", "url": "https://www.naukri.com/rss/keyword-pharmacy-internship", "source": "Naukri"},
    {"name": "Naukri - Pharma Fresher", "url": "https://www.naukri.com/rss/keyword-pharma-fresher", "source": "Naukri"},
    {"name": "Naukri - Pharmacovigilance", "url": "https://www.naukri.com/rss/keyword-pharmacovigilance", "source": "Naukri"},
    {"name": "Naukri - Clinical Research", "url": "https://www.naukri.com/rss/keyword-clinical-research", "source": "Naukri"},
    {"name": "Naukri - Medical Writing", "url": "https://www.naukri.com/rss/keyword-medical-writing", "source": "Naukri"},
    {"name": "Naukri - Regulatory Affairs", "url": "https://www.naukri.com/rss/keyword-regulatory-affairs", "source": "Naukri"},
    {"name": "Naukri - Quality Assurance Pharma", "url": "https://www.naukri.com/rss/keyword-quality-assurance-pharma", "source": "Naukri"},
    {"name": "Naukri - Production Pharma", "url": "https://www.naukri.com/rss/keyword-production-pharma", "source": "Naukri"},
    {"name": "Naukri - R&D Pharma", "url": "https://www.naukri.com/rss/keyword-r%26d-pharma", "source": "Naukri"},

    # ===== TOP INDIAN PHARMA (by revenue/market cap) =====
    # Most use Workday: https://company.wd1.myworkdayjobs.com/rss
    {"name": "Sun Pharma", "url": "https://sunpharma.wd1.myworkdayjobs.com/rss", "source": "Sun Pharma"},
    {"name": "Cipla", "url": "https://cipla.wd1.myworkdayjobs.com/rss", "source": "Cipla"},
    {"name": "Dr. Reddy's Laboratories", "url": "https://drreddys.wd1.myworkdayjobs.com/rss", "source": "Dr. Reddy's"},
    {"name": "Lupin", "url": "https://lupin.wd1.myworkdayjobs.com/rss", "source": "Lupin"},
    {"name": "Zydus Lifesciences", "url": "https://zyduscadila.wd1.myworkdayjobs.com/rss", "source": "Zydus"},
    {"name": "Torrent Pharma", "url": "https://torrentpharma.wd1.myworkdayjobs.com/rss", "source": "Torrent Pharma"},
    {"name": "Alkem Laboratories", "url": "https://alkemlabs.wd1.myworkdayjobs.com/rss", "source": "Alkem Labs"},
    {"name": "Glenmark Pharma", "url": "https://glenmark.wd1.myworkdayjobs.com/rss", "source": "Glenmark"},
    {"name": "Aurobindo Pharma", "url": "https://aurobindo.wd1.myworkdayjobs.com/rss", "source": "Aurobindo"},
    {"name": "Biocon", "url": "https://biocon.wd1.myworkdayjobs.com/rss", "source": "Biocon"},
    {"name": "Abbott India", "url": "https://abbott.wd1.myworkdayjobs.com/rss", "source": "Abbott India"},
    {"name": "Piramal Pharma", "url": "https://piramal.wd1.myworkdayjobs.com/rss", "source": "Piramal"},
    {"name": "Natco Pharma", "url": "https://natcopharma.wd1.myworkdayjobs.com/rss", "source": "Natco"},
    {"name": "Granules India", "url": "https://granules.wd1.myworkdayjobs.com/rss", "source": "Granules"},
    {"name": "Laurus Labs", "url": "https://lauruslabs.wd1.myworkdayjobs.com/rss", "source": "Laurus Labs"},
    {"name": "Suven Pharma", "url": "https://suven.wd1.myworkdayjobs.com/rss", "source": "Suven"},
    {"name": "Ajanta Pharma", "url": "https://ajantapharma.wd1.myworkdayjobs.com/rss", "source": "Ajanta Pharma"},
    {"name": "Ipca Laboratories", "url": "https://ipcalabs.wd1.myworkdayjobs.com/rss", "source": "Ipca Labs"},
    {"name": "Jubilant Pharmova", "url": "https://jubilantpharmova.wd1.myworkdayjobs.com/rss", "source": "Jubilant"},
    {"name": "Strides Pharma", "url": "https://strides.wd1.myworkdayjobs.com/rss", "source": "Strides"},
    {"name": "Alembic Pharma", "url": "https://alembic.wd1.myworkdayjobs.com/rss", "source": "Alembic"},
    {"name": "Eris Lifesciences", "url": "https://erislifesciences.wd1.myworkdayjobs.com/rss", "source": "Eris Lifesciences"},
    {"name": "Mankind Pharma", "url": "https://mankindpharma.wd1.myworkdayjobs.com/rss", "source": "Mankind Pharma"},
    {"name": "Emcure Pharma", "url": "https://emcure.wd1.myworkdayjobs.com/rss", "source": "Emcure"},
    {"name": "FDC Limited", "url": "https://fdcindia.wd1.myworkdayjobs.com/rss", "source": "FDC"},
    {"name": "Unichem Labs", "url": "https://unichemlabs.wd1.myworkdayjobs.com/rss", "source": "Unichem"},
    {"name": "Wockhardt", "url": "https://wockhardt.wd1.myworkdayjobs.com/rss", "source": "Wockhardt"},
    {"name": "Gufic Biosciences", "url": "https://gufic.wd1.myworkdayjobs.com/rss", "source": "Gufic"},
    {"name": "Caplin Point", "url": "https://caplinpoint.wd1.myworkdayjobs.com/rss", "source": "Caplin Point"},
    {"name": "SeQuent Scientific", "url": "https://sequent.wd1.myworkdayjobs.com/rss", "source": "SeQuent"},
    {"name": "Solara Active Pharma", "url": "https://solara.wd1.myworkdayjobs.com/rss", "source": "Solara"},
    {"name": "Neuland Labs", "url": "https://neulandlabs.wd1.myworkdayjobs.com/rss", "source": "Neuland Labs"},

    # ===== MNC PHARMA WITH STRONG INDIA OPS =====
    {"name": "Pfizer India", "url": "https://pfizer.wd1.myworkdayjobs.com/rss", "source": "Pfizer India"},
    {"name": "Novartis India", "url": "https://novartis.wd1.myworkdayjobs.com/rss", "source": "Novartis India"},
    {"name": "GSK India", "url": "https://gsk.wd1.myworkdayjobs.com/rss", "source": "GSK India"},
    {"name": "Sanofi India", "url": "https://sanofi.wd1.myworkdayjobs.com/rss", "source": "Sanofi India"},
    {"name": "Merck India", "url": "https://merck.wd1.myworkdayjobs.com/rss", "source": "Merck India"},
    {"name": "Boehringer Ingelheim India", "url": "https://boehringer-ingelheim.wd1.myworkdayjobs.com/rss", "source": "Boehringer Ingelheim"},
    {"name": "Bristol Myers Squibb India", "url": "https://bms.wd1.myworkdayjobs.com/rss", "source": "BMS India"},
    {"name": "Eli Lilly India", "url": "https://lilly.wd1.myworkdayjobs.com/rss", "source": "Eli Lilly India"},
    {"name": "AstraZeneca India", "url": "https://astrazeneca.wd1.myworkdayjobs.com/rss", "source": "AstraZeneca India"},
    {"name": "Roche India", "url": "https://roche.wd1.myworkdayjobs.com/rss", "source": "Roche India"},
    {"name": "Johnson & Johnson India", "url": "https://jnj.wd1.myworkdayjobs.com/rss", "source": "J&J India"},
    {"name": "Takeda India", "url": "https://takeda.wd1.myworkdayjobs.com/rss", "source": "Takeda India"},
    {"name": "Viatris India", "url": "https://viatris.wd1.myworkdayjobs.com/rss", "source": "Viatris India"},
    {"name": "Bayer India", "url": "https://bayer.wd1.myworkdayjobs.com/rss", "source": "Bayer India"},

    # ===== CROs / CLINICAL RESEARCH / PHARMACOVIGILANCE =====
    {"name": "IQVIA India", "url": "https://iqvia.wd1.myworkdayjobs.com/rss", "source": "IQVIA"},
    {"name": "Parexel India", "url": "https://parexel.wd1.myworkdayjobs.com/rss", "source": "Parexel"},
    {"name": "Syneos Health India", "url": "https://syneoshealth.wd1.myworkdayjobs.com/rss", "source": "Syneos Health"},
    {"name": "ICON plc India", "url": "https://iconplc.wd1.myworkdayjobs.com/rss", "source": "ICON"},
    {"name": "PPD India", "url": "https://ppd.wd1.myworkdayjobs.com/rss", "source": "PPD"},
    {"name": "Medpace India", "url": "https://medpace.wd1.myworkdayjobs.com/rss", "source": "Medpace"},
    {"name": "Syneos Health", "url": "https://syneoshealth.wd1.myworkdayjobs.com/rss", "source": "Syneos Health"},
    {"name": "Covance India", "url": "https://covance.wd1.myworkdayjobs.com/rss", "source": "Covance"},
    {"name": "ClinChoice India", "url": "https://clinchoice.wd1.myworkdayjobs.com/rss", "source": "ClinChoice"},
    {"name": "Veeda Clinical Research", "url": "https://veeda.wd1.myworkdayjobs.com/rss", "source": "Veeda"},
    {"name": "Lambda Therapeutic", "url": "https://lambda.wd1.myworkdayjobs.com/rss", "source": "Lambda"},
    {"name": "Siro Clinpharm", "url": "https://siroclinpharm.wd1.myworkdayjobs.com/rss", "source": "Siro Clinpharm"},
    {"name": "Accutest Research", "url": "https://accutest.wd1.myworkdayjobs.com/rss", "source": "Accutest"},
    {"name": "CliniRx Research", "url": "https://clininrx.wd1.myworkdayjobs.com/rss", "source": "CliniRx"},

    # ===== PHARMACOVIGILANCE / DRUG SAFETY SPECIALISTS =====
    {"name": "Cognizant PV", "url": "https://cognizant.wd1.myworkdayjobs.com/rss", "source": "Cognizant"},
    {"name": "TCS Life Sciences", "url": "https://tcs.wd1.myworkdayjobs.com/rss", "source": "TCS"},
    {"name": "Wipro Life Sciences", "url": "https://wipro.wd1.myworkdayjobs.com/rss", "source": "Wipro"},
    {"name": "Accenture Life Sciences", "url": "https://accenture.wd1.myworkdayjobs.com/rss", "source": "Accenture"},
    {"name": "Genpact PV", "url": "https://genpact.wd1.myworkdayjobs.com/rss", "source": "Genpact"},
    {"name": "EXL Health", "url": "https://exl.wd1.myworkdayjobs.com/rss", "source": "EXL"},
    {"name": "IQVIA Vigilance", "url": "https://iqvia.wd1.myworkdayjobs.com/rss", "source": "IQVIA Vigilance"},

    # ===== MEDICAL WRITING / MEDICAL AFFAIRS =====
    {"name": "Cactus Communications", "url": "https://cactusglobal.wd1.myworkdayjobs.com/rss", "source": "Cactus Communications"},
    {"name": "Indegene", "url": "https://indegene.wd1.myworkdayjobs.com/rss", "source": "Indegene"},
    {"name": "Eliassen Group", "url": "https://eliassen.wd1.myworkdayjobs.com/rss", "source": "Eliassen"},
    {"name": "Syneos Health Med Affairs", "url": "https://syneoshealth.wd1.myworkdayjobs.com/rss", "source": "Syneos Med Affairs"},

    # ===== REGULATORY AFFAIRS COMPANIES =====
    {"name": "Freyr Solutions", "url": "https://freyrsolutions.wd1.myworkdayjobs.com/rss", "source": "Freyr"},
    {"name": "Tata Elxsi Regulatory", "url": "https://tataelxsi.wd1.myworkdayjobs.com/rss", "source": "Tata Elxsi"},
    {"name": "Criterium Inc", "url": "https://criterium.wd1.myworkdayjobs.com/rss", "source": "Criterium"},

    # ===== BIOTECH / BIOSIMILARS / VACCINES =====
    {"name": "Biocon Biologics", "url": "https://bioconbiologics.wd1.myworkdayjobs.com/rss", "source": "Biocon Biologics"},
    {"name": "Enzene Biosciences", "url": "https://enzene.wd1.myworkdayjobs.com/rss", "source": "Enzene"},
    {"name": "Reliance Life Sciences", "url": "https://reliancelifesciences.wd1.myworkdayjobs.com/rss", "source": "Reliance Life Sciences"},
    {"name": "Bharat Biotech", "url": "https://bharatbiotech.wd1.myworkdayjobs.com/rss", "source": "Bharat Biotech"},
    {"name": "Serum Institute", "url": "https://seruminstitute.wd1.myworkdayjobs.com/rss", "source": "Serum Institute"},
    {"name": "Panacea Biotec", "url": "https://panaceabiotec.wd1.myworkdayjobs.com/rss", "source": "Panacea Biotec"},
    {"name": "Indian Immunologicals", "url": "https://indianimmunologicals.wd1.myworkdayjobs.com/rss", "source": "Indian Immunologicals"},
    {"name": "Hester Biosciences", "url": "https://hesterbiosciences.wd1.myworkdayjobs.com/rss", "source": "Hester Biosciences"},

    # ===== API / INTERMEDIATES / CDMO =====
    {"name": "Laurus Labs", "url": "https://lauruslabs.wd1.myworkdayjobs.com/rss", "source": "Laurus Labs"},
    {"name": "Suven Pharma", "url": "https://suven.wd1.myworkdayjobs.com/rss", "source": "Suven Pharma"},
    {"name": "SeQuent Scientific", "url": "https://sequent.wd1.myworkdayjobs.com/rss", "source": "SeQuent Scientific"},
    {"name": "Solara Active Pharma", "url": "https://solara.wd1.myworkdayjobs.com/rss", "source": "Solara"},
    {"name": "Neuland Labs", "url": "https://neulandlabs.wd1.myworkdayjobs.com/rss", "source": "Neuland Labs"},
    {"name": "Granules India", "url": "https://granules.wd1.myworkdayjobs.com/rss", "source": "Granules India"},
    {"name": "Divis Labs", "url": "https://divislabs.wd1.myworkdayjobs.com/rss", "source": "Divis Labs"},
    {"name": "Aarti Drugs", "url": "https://aartidrugs.wd1.myworkdayjobs.com/rss", "source": "Aarti Drugs"},

    # ===== GOVERNMENT / REGULATORY / ACADEMIC =====
    # These typically don't have RSS - check manually
    # {"name": "AICTE Internship Portal", "url": "https://internship.aicte-india.org", "source": "AICTE"},
    # {"name": "Pharmacy Council of India", "url": "https://pci.nic.in", "source": "PCI"},
    # {"name": "CDSCO", "url": "https://cdsco.gov.in", "source": "CDSCO"},
    # {"name": "ICMR", "url": "https://icmr.gov.in", "source": "ICMR"},
    # {"name": "NIPER", "url": "https://niper.gov.in", "source": "NIPER"},
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
    "industrial trainee", "project trainee",
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
            r"\b([A-Z][a-z]+,\s*[A-Z]{2,})\b",
            r"\b(Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Pune|Kolkata|Ahmedabad|Gurgaon|Noida|Navi Mumbai|Thane|Vadodara|Surat|Rajkot|Bhavnagar|Jamnagar|Ankleshwar|Vapi|Dahej|Panoli|Sachin|Vizag|Visakhapatnam|Goa|Mysore|Coimbatore|Kochi|Trivandrum|Bhubaneswar|Guwahati|Indore|Bhopal|Raipur|Ranchi|Patna|Lucknow|Kanpur|Nagpur|Nashik|Aurangabad)\b",
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
