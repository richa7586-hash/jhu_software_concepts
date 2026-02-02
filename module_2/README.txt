# JHED ID A68B60

# jhu_software_concepts - Module 2 - Web Scraping - Due by Feb 1, 2026


# How It Works
List Page Parsing: Scrapes the main results table to extract basic information and result IDs
Detail Page Fetching: For each result, fetches the individual detail page
Data Extraction: Parses HTML to extract all available fields
Data Storage: Appends results to a JSON file for persistence

# Requirements
- Python 3.10+
- pip

# Setup
1) Change into the app folder:
   cd module2
2) Create and activate a virtual environment (optional but recommended):
   python -m venv venv
   source venv/bin/activate
3) Install dependencies:
   pip install -r requirements.txt

4) to run
    python main.py

## 🤖 robots.txt Compliance

This scraper complies with The Grad Cafe's robots.txt file:
- Crawling is **allowed** (`Allow: /`)
- Implements rate limiting (1 second between requests)
- **Content Signal**: `search=yes, ai-train=no`
  - Data collection for research: **Permitted**
  - Using data for AI training: **Not Permitted**

**Screenshot Evidence**: See `robots_txt_screenshots.pdf` for verification.
