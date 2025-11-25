import os
import sys

# Add the src directory to the python path
# Current file is in src/discovery_agent/main.py
# We want to add src/ to the path
current_dir = os.path.dirname(os.path.abspath(__file__)) # src/discovery_agent
src_dir = os.path.dirname(current_dir) # src
sys.path.append(src_dir)

from discovery_agent.utils.logging_setup import setup_logging
from discovery_agent.utils.excel_writer import ExcelWriter
from discovery_agent.scrapers.job_postings import JobPostingScraper
# from discovery_agent.scrapers.certificates_of_occupancy import CertificateOfOccupancyScraper
from discovery_agent.scrapers.real_estate_news import RealEstateDiscovery
from discovery_agent.scrapers.funding_news import FundingNewsDiscovery

def main():
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    setup_logging(os.path.join("logs", "discovery_agent.log"))
    print("Starting Discovery Agent...")
    
    # Initialize Excel Repository
    if not os.path.exists("data"):
        os.makedirs("data")
    
    excel_writer = ExcelWriter(os.path.join("data", "leads_repository.xlsx"))
    
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
    
    # Save to Excel
    print(f"\nSaving total {len(all_new_leads)} leads to Excel...")
    excel_writer.save_leads(all_new_leads)
    print("Discovery process completed.")

if __name__ == "__main__":
    main()
