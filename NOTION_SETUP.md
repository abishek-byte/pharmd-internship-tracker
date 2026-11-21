 # Notion Database Setup Guide

 ## 1. Create a New Database in Notion

 1. Open Notion → Create a new **Page** → Choose **Table - Full page**
 2. Name it "PharmD Internship Tracker"
 3. Add the following **properties** (exact names matter — the script uses these):

 | Property Name | Type | Notes |
 |---------------|------|-------|
 | **Title** | Title | Required — main job title |
 | **Company** | Text | Employer name |
 | **Location** | Text | City, State or "Remote" |
 | **URL** | URL | Link to job posting |
 | **Source** | Select | Options: Indeed, ASHP, ACCP, LinkedIn, CVS Health, Walgreens, etc. |
 | **Status** | Select | Options: **New**, Applied, Interviewing, Offer, Rejected, Archived |
 | **Posted Date** | Date | Auto-filled from RSS |
 | **Description** | Text | Job description snippet |
 | **Notes** | Text | *Optional* — your personal notes |
 | **Contact** | Text | *Optional* — recruiter/hiring manager |
 | **Deadline** | Date | *Optional* — application deadline |

 4. Set **Status** default to "New"
 5. Add a few **Select options** for Source: Indeed, ASHP, ACCP, LinkedIn, CVS Health, Walgreens, Other

 ## 2. Get Your Database ID

 1. Open the database in Notion (full page view)
 2. URL looks like: `https://www.notion.so/your-workspace/Database-Name-**<DATABASE_ID>**?v=...`
 3. Copy the **32-character ID** after the last `/` and before `?v=`
    - Example: `a1b2c3d4e5f6789012345678901234ab`

 ## 3. Create a Notion Integration

 1. Go to https://www.notion.so/my-integrations
 2. Click **+ New integration**
 3. Name: "PharmD Job Tracker"
 4. Associated workspace: select yours
 5. **Capabilities**: Read content, Update content, Insert content
 6. Click **Submit** → Copy the **Internal Integration Secret** (starts with `secret_`)

 ## 4. Connect Integration to Database

 1. Open your database page in Notion
 2. Click **•••** (top right) → **Connections** → **Add connections**
 3. Search for "PharmD Job Tracker" → **Confirm**

 ## 5. Add Secrets to GitHub

 1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
 2. Click **New repository secret** (add both):
    - `NOTION_TOKEN` = your `secret_xxx` integration token
    - `NOTION_DB_ID` = the 32-char database ID

 ## 6. Test It

 ```bash
 # Local test (requires .env file with NOTION_TOKEN and NOTION_DB_ID)
 pip install -r requirements.txt
 python fetch_jobs.py
 ```

 Or trigger manually in GitHub: **Actions** → **Fetch PharmD Internships** → **Run workflow**

 ## 7. Customize RSS Feeds (in `fetch_jobs.py`)

 Edit the `RSS_FEEDS` list to add your own searches:

 **Indeed custom search:**
 1. Go to indeed.com → search "PharmD intern" + your city
 2. Click **"Get RSS feed"** (bottom right) → copy URL
 3. Add to `RSS_FEEDS` in `fetch_jobs.py`

 **LinkedIn (via RSS Bridge):**
 - LinkedIn doesn't offer public RSS. Options:
   - Self-host [RSS-Bridge](https://github.com/RSS-Bridge/rss-bridge) → LinkedIn bridge
   - Use email-to-RSS (e.g., kill-the-newsletter.com) → forward LinkedIn job alerts
   - Manual: copy job URLs into Notion

 **Handshake (university):**
 - Some schools expose RSS. Check your career center.
 - Or: forward Handshake email alerts to an email-to-RSS service.

 **Company career pages:**
 - Many ATS (Workday, Greenhouse, Lever) expose RSS at `/rss` or `/feed`
 - Test: visit `https://jobs.company.com/rss` or `https://company.wd1.myworkdayjobs.com/rss`

 ## 8. Adjust Keywords (in `fetch_jobs.py`)

 Modify `INCLUDE_KEYWORDS` / `EXCLUDE_KEYWORDS` to match your interests:
 - Add: "oncology", "infectious disease", "critical care", "pharmacogenomics"
 - Remove: "nuclear pharmacy" (if not interested)

 ## 9. Dashboard Views (Notion)

 Create linked views for different workflows:
 - **Kanban by Status** — drag cards through pipeline
 - **Calendar by Deadline** — visualize due dates
 - **Table grouped by Source** — see which channels perform
 - **Filtered: Status = "New"** — your daily action list

 ## 10. Optional Enhancements

 - **Auto-archive old jobs**: Add a GitHub Action that marks jobs > 60 days as "Archived"
 - **Slack/Email notifications**: Add a step to post new jobs to a Slack webhook
 - **Cover letter generator**: Use Notion AI or a separate script to draft tailored letters
 - **Interview prep**: Add a "Interview Date" property + linked "Prep Notes" page template
