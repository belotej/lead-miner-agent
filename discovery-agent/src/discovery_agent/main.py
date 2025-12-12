import os
import sys

# Add the src directory to the python path
# Current file is in src/discovery_agent/main.py
# We want to add src/ to the path
current_dir = os.path.dirname(os.path.abspath(__file__)) # src/discovery_agent
src_dir = os.path.dirname(current_dir) # src
sys.path.append(src_dir)

# Project root is two levels up from this file (src/discovery_agent/main.py -> discovery-agent/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(current_dir))

from discovery_agent.utils.logging_setup import setup_logging
from discovery_agent.utils.excel_writer import ExcelWriter
from discovery_agent.utils.db_writer import DatabaseWriter
from discovery_agent.scrapers.job_postings import JobPostingScraper
# from discovery_agent.scrapers.certificates_of_occupancy import CertificateOfOccupancyScraper
from discovery_agent.scrapers.real_estate_news import RealEstateDiscovery
from discovery_agent.scrapers.funding_news import FundingNewsDiscovery

def main():
    # Ensure logs directory exists (relative to project root)
    logs_dir = os.path.join(PROJECT_ROOT, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    setup_logging(os.path.join(logs_dir, "discovery_agent.log"))
    print("Starting Discovery Agent...")

    # Initialize Excel Repository (relative to project root)
    data_dir = os.path.join(PROJECT_ROOT, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    excel_writer = ExcelWriter(os.path.join(data_dir, "leads_repository.xlsx"))

    # Initialize Database Writer
    try:
        db_writer = DatabaseWriter()
        use_database = True
        print(f"Database connected. Current lead count: {db_writer.get_lead_count()}")
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Continuing with Excel-only mode.")
        use_database = False

    all_new_leads = []

    # 1. Job Postings
    print("\n--- Running Job Posting Scraper ---")
    job_scraper = JobPostingScraper()
    job_leads = job_scraper.run()
    print(f"Found {len(job_leads)} leads from job postings.")
    all_new_leads.extend(job_leads)

    # 2. Real Estate Signals
    print("\n--- Running Real Estate Signal Discovery ---")
    re_discovery = RealEstateDiscovery()
    re_leads = re_discovery.run()
    print(f"Found {len(re_leads)} leads from real estate news.")
    all_new_leads.extend(re_leads)

    # 3. Funding Signals
    print("\n--- Running Funding News Discovery ---")
    funding_discovery = FundingNewsDiscovery()
    funding_leads = funding_discovery.run()
    print(f"Found {len(funding_leads)} leads from funding news.")
    all_new_leads.extend(funding_leads)

    # Save to Excel (always)
    print(f"\nSaving total {len(all_new_leads)} leads to Excel...")
    excel_writer.save_leads(all_new_leads)

    # Save to Database (if available)
    if use_database:
        print("Saving leads to database...")
        saved, skipped = db_writer.save_leads(all_new_leads)
        print(f"Database: {saved} new leads saved, {skipped} duplicates skipped.")
        print(f"Total leads in database: {db_writer.get_lead_count()}")

    print("\nDiscovery process completed.")
    if use_database:
        print("View leads at: http://127.0.0.1:8000/admin/leads/lead/")

if __name__ == "__main__":
    main()
