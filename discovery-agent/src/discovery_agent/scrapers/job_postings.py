import requests
import time
import random
from datetime import datetime
import logging
import yaml
import os

class JobPostingScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.rapidapi_key = self.config['api_keys'].get('rapidapi_key', '')
        self.base_url = "https://jsearch.p.rapidapi.com/search"
        
        self.target_titles = self.config['job_posting']['target_titles']
        self.location = "Dallas, TX"
        
    def _load_config(self):
        # Load config from yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to 'discovery-agent' folder
        # src/discovery_agent/scrapers -> src/discovery_agent -> src -> discovery-agent
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        config_path = os.path.join(root_dir, 'config', 'config.yaml')
        
        if not os.path.exists(config_path):
            # Try one level higher just in case
             root_dir = os.path.dirname(root_dir)
             config_path = os.path.join(root_dir, 'config', 'config.yaml')

        if not os.path.exists(config_path):
            # Try CWD fallback
            config_path = "config/config.yaml"
            
        if not os.path.exists(config_path):
             raise FileNotFoundError(f"Config file not found.")
             
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def run(self):
        self.logger.info("Running Job Posting Scraper via JSearch (RapidAPI)...")
        all_leads = []
        
        if not self.rapidapi_key or self.rapidapi_key == "YOUR_RAPIDAPI_KEY":
            self.logger.error("RapidAPI key not configured in config.yaml")
            return []

        for title in self.target_titles:
            self.logger.info(f"Searching for title: {title}")
            leads = self.search_jsearch(title)
            all_leads.extend(leads)
            # Be polite
            time.sleep(2)
            
        return all_leads

    def search_jsearch(self, job_title):
        leads = []
        
        query = f"{job_title} in {self.location}"
        
        querystring = {
            "query": query,
            "page": "1",
            "num_pages": "1", 
            "date_posted": "month" # Get fresh jobs from last month
        }

        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=querystring)
            
            if response.status_code != 200:
                self.logger.error(f"JSearch API Error: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            
            if 'data' not in data:
                self.logger.info(f"No results found for {job_title}")
                return []
                
            for item in data['data']:
                lead = self._parse_jsearch_result(item)
                if lead:
                    leads.append(lead)
                    
        except Exception as e:
            self.logger.error(f"Error searching JSearch for {job_title}: {e}")
            
        return leads
    
    def _parse_jsearch_result(self, item):
        try:
            job_title = item.get('job_title', 'Unknown')
            employer_name = item.get('employer_name', 'Unknown')
            job_city = item.get('job_city', '')
            job_state = item.get('job_state', '')
            job_posted_at = item.get('job_posted_at_datetime_utc', '')
            job_apply_link = item.get('job_apply_link', '')
            job_description = item.get('job_description', '')
            
            location = f"{job_city}, {job_state}" if job_city and job_state else self.location
            
            # Basic signal strength logic
            signal_strength = "Medium"
            if "VP" in job_title or "Director" in job_title or "Head" in job_title:
                signal_strength = "High"
            elif "Manager" not in job_title:
                signal_strength = "Low"

            # Format date
            try:
                if job_posted_at:
                    dt = datetime.strptime(job_posted_at.split('T')[0], "%Y-%m-%d")
                    posted_date = dt.strftime("%Y-%m-%d")
                else:
                    posted_date = datetime.now().strftime("%Y-%m-%d")
            except:
                posted_date = datetime.now().strftime("%Y-%m-%d")

            lead = {
                "discovery_date": datetime.now().strftime("%Y-%m-%d"),
                "company_name": employer_name,
                "domain": item.get('employer_website', ''), # JSearch sometimes provides this!
                "discovery_source": "jsearch_api",
                "signal_type": "hiring",
                "signal_strength": signal_strength,
                "signal_date": posted_date,
                "details": f"Hiring for {job_title}",
                "location": location,
                "timeline": "Unknown",
                "source_url": job_apply_link,
                "county": "",
                "all_signals": "job_posting",
                "notes": f"Description snippet: {job_description[:100]}..."
            }
            return lead
            
        except Exception as e:
            self.logger.error(f"Error parsing item: {e}")
            return None
