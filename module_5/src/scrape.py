"""Scrape applicant data from The Grad Cafe."""

import json
import time
import re
import os
from urllib.parse import urljoin
from urllib3 import request
from urllib3.exceptions import HTTPError
from bs4 import BeautifulSoup

from clean import clean_data
import load_data
from model import ApplicantData
import config


class GradCafeScraper:
    """Scraper for The Grad Cafe applicant data"""

    def __init__(self):
        self.base_url = config.BASE_URL.rstrip('/')
        self.list_url_template = config.LIST_URL_TEMPLATE
        self.data_file = config.DATA_FILE

    # ==================== Fetching Methods ====================

    def fetch_page(self, url):
        """Fetch HTML content from URL using urllib3"""
        try:
            resp = request("GET", url)
            html = resp.data.decode("utf-8")
            return html

        except (HTTPError, OSError, UnicodeDecodeError) as e:
            print(f"Error fetching {url}: {e}")
            return None

    # ==================== Parsing Methods ====================

    def parse_list_page(self, html):
        """Extract result IDs and basic info from list page"""
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        if not table:
            print("No table found on page")
            return []

        results = []
        all_rows = table.find_all('tr')

        i = 0
        while i < len(all_rows):
            row = all_rows[i]
            cells = row.find_all('td')

            # Look for the main data row (has 5 cells with "See More" link)
            if len(cells) == 5:
                # This is a main data row
                see_more_link = cells[-1].find('a', href=re.compile(r'^/result/\d+$'))

                if see_more_link:
                    # Create ApplicantData object
                    applicant = ApplicantData()
                    applicant.result_id = see_more_link.get('href').split('/result/')[-1]
                    applicant.url = urljoin(self.base_url, see_more_link.get('href'))

                    try:
                        # Cell 0: University
                        university_div = cells[0].find('div', class_='tw-font-medium')
                        if university_div:
                            applicant.university = university_div.get_text(strip=True)

                        # Cell 1: Program and Degree
                        program_div = cells[1].find('div', class_='tw-text-gray-900')
                        if program_div:
                            spans = program_div.find_all('span')
                            if len(spans) >= 1 and university_div:
                                applicant.program = spans[0].get_text(strip=True) + ', ' + \
                                                    university_div.get_text(strip=True)
                            if len(spans) >= 2:
                                applicant.masters_or_phd = spans[1].get_text(strip=True)

                        # Cell 2: Date Added
                        applicant.date_added = cells[2].get_text(strip=True)

                    except Exception as e:
                        print(f"Error parsing basic info for result {applicant.result_id}: {e}")

                    # Now look for the badge row (next row with colspan="3")
                    if i + 1 < len(all_rows):
                        next_row = all_rows[i + 1]
                        next_cells = next_row.find_all('td')

                        if len(next_cells) > 0 and next_cells[0].get('colspan') == '3':
                            try:
                                badges = next_cells[0].find_all('div', class_='tw-inline-flex')
                                for badge in badges:
                                    badge_text = badge.get_text(strip=True)

                                    # Parse status (first badge with md:tw-hidden class)
                                    if 'md:tw-hidden' in badge.get('class', []):
                                        self._parse_status_info(badge_text, applicant)
                                        continue

                                    # Parse semester/year
                                    semester_match = re.search(r'(Fall|Spring|Summer)\s+(\d{4})',
                                                               badge_text)
                                    if semester_match:
                                        applicant.semester_year_start = \
                                            f"{semester_match.group(1)} {semester_match.group(2)}"
                                        continue

                                    # Parse student type
                                    if badge_text in ['American', 'International']:
                                        applicant.citizenship = badge_text
                                        continue

                                    # Parse GPA
                                    gpa_match = re.search(r'GPA\s+(\d+\.?\d*)', badge_text)
                                    if gpa_match:
                                        applicant.gpa = gpa_match.group(1)
                                        continue

                            except Exception as e:
                                print(f"Error parsing badges for result {applicant.result_id}: {e}")

                    results.append(applicant)

            i += 1

        return results

    def parse_detail_page(self, html, applicant):
        """Extract detailed info from individual result page"""
        soup = BeautifulSoup(html, 'html.parser')

        try:
            # Extract Notes/Comments
            notes_dt = soup.find('dt', string='Notes')
            if notes_dt:
                notes_dd = notes_dt.find_next_sibling('dd')
                if notes_dd:
                    notes_text = notes_dd.get_text(strip=True)
                    if notes_text and len(notes_text) > 5:
                        applicant.comments = notes_text

            def parse_numeric_value(text):
                match = re.search(r"\d+(\.\d+)?", text)
                if not match:
                    return None
                try:
                    return float(match.group(0))
                except ValueError:
                    return None

            # Extract GRE scores using the list item structure
            gre_items = soup.find_all("li", class_=re.compile(r"tw-flex"))
            for item in gre_items:
                label_span = item.find("span", class_=re.compile(r"tw-font-medium"))
                value_span = item.find("span", class_=re.compile(r"tw-text-gray-400"))
                if not label_span or not value_span:
                    continue

                label_text = label_span.get_text(strip=True)
                value_text = value_span.get_text(strip=True)
                numeric_value = parse_numeric_value(value_text)
                if numeric_value is None or numeric_value <= 0:
                    continue

                if "GRE General" in label_text:
                    applicant.gre = str(numeric_value)
                elif "GRE Verbal" in label_text:
                    applicant.gre_v = str(numeric_value)
                elif "Analytical Writing" in label_text:
                    applicant.gre_aw = str(numeric_value)
                elif "Undergrad GPA" in label_text:
                    applicant.gpa = str(numeric_value)

            # Extract notification date (if not already set)
            if not applicant.decision_date:
                page_text = soup.get_text()
                notification_match = re.search(r'Notification\s+on[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
                                               page_text,
                                               re.IGNORECASE)
                if notification_match:
                    applicant.decision_date = notification_match.group(1)

            # Extract student type (Degree's Country of Origin) if not already set
            if not applicant.citizenship:
                origin_dt = soup.find("dt", string=re.compile(r"Degree'?s\s+Country\s+of\s+Origin",
                                                              re.IGNORECASE))
                if origin_dt:
                    origin_dd = origin_dt.find_next_sibling("dd")
                    if origin_dd:
                        origin_text = origin_dd.get_text(strip=True)
                        if origin_text:
                            applicant.citizenship = origin_text

        except Exception as e:
            print(f"Error parsing detail page for result {applicant.result_id}: {e}")

    # ==================== Helper Methods ====================

    def _parse_status_info(self, text, applicant):
        """Parse status, dates, semester, student type from status text"""

        # Extract status and status date
        status_patterns = [
            (r'Accepted\s+on\s+(.+?)(?=Fall|Spring|Summer|American|International|GPA|$)',
             'Accepted'),
            (r'Rejected\s+on\s+(.+?)(?=Fall|Spring|Summer|American|International|GPA|$)',
             'Rejected'),
            (r'Interview\s+on\s+(.+?)(?=Fall|Spring|Summer|American|International|GPA|$)',
             'Interview'),
            (r'Wait\s*listed\s+on\s+(.+?)(?=Fall|Spring|Summer|American|International|GPA|$)',
             'Wait listed'),
        ]

        for pattern, status_value in status_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                applicant.status = status_value
                applicant.decision_date = match.group(1).strip()
                break

        # Extract semester and year
        semester_match = re.search(r'(Fall|Spring|Summer)\s+(\d{4})', text)
        if semester_match:
            applicant.semester_year_start = f"{semester_match.group(1)} {semester_match.group(2)}"

        # Extract student type
        if re.search(r'\bAmerican\b', text):
            applicant.citizenship = 'American'
        elif re.search(r'\bInternational\b', text):
            applicant.citizenship = 'International'

        # Extract GPA from status text
        gpa_match = re.search(r'GPA\s+(\d+\.?\d*)', text)
        if gpa_match:
            applicant.gpa = gpa_match.group(1)

    # ==================== Data Persistence ====================

    def save_data(self, applicant_list):
        """Append applicant data to JSON file"""
        try:
            # Read existing data
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []

            # Append new records
            for applicant in applicant_list:
                data.append(applicant.to_dict())

            # Write back to file
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Saved {len(applicant_list)} records. Total: {len(data)}")

        except Exception as e:
            print(f"Error saving data: {e}")

    # ==================== Main Scraping Method ====================

    def scrape_page(self, page_num):
        """Scrape a single page (list + all detail pages)"""
        print(f"{'=' * 60}")
        print(f"Scraping page {page_num}")
        print(f"{'=' * 60}")

        # Fetch list page
        list_url = self.list_url_template.format(page_num)
        html = self.fetch_page(list_url)
        if not html:
            print(f"Failed to fetch page {page_num}")
            return []

        # Parse list page
        applicants = self.parse_list_page(html)
        print(f"Found {len(applicants)} results on page {page_num}")

        if not applicants:
            return []

        # Fetch detail pages
        for i, applicant in enumerate(applicants, 1):
            print(f"    [{i}/{len(applicants)}] Fetching details for result \
                    {applicant.result_id}...", end=' ')

            detail_html = self.fetch_page(applicant.url)
            if detail_html:
                self.parse_detail_page(detail_html, applicant)
                print("Success")
            else:
                print("Failed")

        return applicants

    def pull_data(self, max_seconds=10):
        """Scrape list pages starting from page 1 for up to max_seconds.
        Once pull is complete, run clean_data.py to clean and save data to JSON file."""
        start_time = time.time()
        page_num = 1
        total_records = 0
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

        while time.time() - start_time < max_seconds:
            applicants = self.scrape_page(page_num)
            if not applicants:
                print(f"No results found on page {page_num}. Continuing.")
                page_num += 1
                continue

            self.save_data(applicants)
            total_records += len(applicants)
            page_num += 1

        elapsed = time.time() - start_time
        print(f"Pull complete. Pages scraped: {page_num - 1},"
              f"records saved: {total_records}, time: {elapsed:.1f}s")
        llm_script_path = os.path.join(os.path.dirname(__file__), "../llm_hosting", "app.py")
        clean_data(
            input_file=self.data_file,
            llm_script_path=llm_script_path,
            output_file=config.APPLICANT_DATA_JSON_FILE,
        )
        load_data.main()


if __name__ == "__main__":
    GradCafeScraper().pull_data()
