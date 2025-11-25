import requests
from datetime import datetime, timedelta
import logging
import yaml
import os
import urllib.parse

class CertificateOfOccupancyScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.base_url = "https://www.dallasopendata.com/resource/dryn-sntn.json"
        self.min_sqft = self.config['public_records'].get('co_min_sqft', 5000)
        self.lookback_days = self.config['public_records'].get('lookback_days', 90) # Increase default lookback for testing
        
    def _load_config(self):
        # Robust config loading
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # src/discovery_agent/scrapers -> src/discovery_agent -> src -> discovery-agent
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        config_path = os.path.join(root_dir, 'config', 'config.yaml')
        
        if not os.path.exists(config_path):
             root_dir = os.path.dirname(root_dir)
             config_path = os.path.join(root_dir, 'config', 'config.yaml')
             
        if not os.path.exists(config_path):
            config_path = "config/config.yaml"
            
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def run(self):
        self.logger.info("Running Certificate of Occupancy Scraper (Dallas)...")
        
        # Calculate date threshold
        threshold_date = (datetime.now() - timedelta(days=self.lookback_days)).strftime("%Y-%m-%dT00:00:00")
        
        # Construct SoQL Query
        # We want:
        # 1. Issued recently
        # 2. Sq Ft > threshold
        # 3. Not cancelled/revoked (status check if available, otherwise just date_issued)
        
        where_clause = f"date_issued >= '{threshold_date}' AND sq_ft >= {self.min_sqft}"
        
        params = {
            "$where": where_clause,
            "$limit": 1000,
            "$order": "date_issued DESC"
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"Dallas API Error: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            self.logger.info(f"Fetched {len(data)} raw CO records.")
            
            leads = []
            for item in data:
                lead = self._parse_record(item)
                if lead:
                    leads.append(lead)
                    
            return leads
            
        except Exception as e:
            self.logger.error(f"Error fetching COs: {e}")
            return []

    def _parse_record(self, item):
        try:
            business_name = item.get('business_name', 'Unknown')
            sq_ft_str = item.get('sq_ft', '0')
            land_use = item.get('land_use', 'Unknown')
            date_issued = item.get('date_issued', '')
            address = item.get('address', '')
            
            # Filter Logic (Client Side)
            # Only interested in OFFICE, MEDICAL OFFICE, COMMERCIAL, etc.
            # Exclude WAREHOUSE if not desired (often has huge sqft but low furniture need)
            
            relevant_uses = ["OFFICE", "MEDICAL", "CLINIC", "COMMERCIAL", "FINANCIAL", "INSTITUTION"]
            is_relevant = any(use in land_use.upper() for use in relevant_uses)
            
            if not is_relevant:
                # Optional: skip if strict, but sometimes land_use is generic.
                # Let's log it but keep it if sqft is high enough, maybe tag it
                pass

            sq_ft = int(sq_ft_str) if sq_ft_str.isdigit() else 0
            
            # Signal Strength Logic
            signal_strength = "Medium"
            if sq_ft > 10000:
                signal_strength = "Very High"
            elif sq_ft > 5000:
                signal_strength = "High"
                
            # Format Date
            if date_issued:
                iso_date = date_issued.split('T')[0]
            else:
                iso_date = datetime.now().strftime("%Y-%m-%d")

            lead = {
                "discovery_date": datetime.now().strftime("%Y-%m-%d"),
                "company_name": business_name,
                "domain": "", 
                "discovery_source": "dallas_co_api",
                "signal_type": "new_occupancy",
                "signal_strength": signal_strength,
                "signal_date": iso_date,
                "details": f"New CO for {sq_ft} sqft. Land Use: {land_use}",
                "location": f"{address}, Dallas, TX",
                "timeline": "Immediate (Move-in)",
                "source_url": "https://www.dallasopendata.com/widgets/dryn-sntn",
                "county": "Dallas",
                "all_signals": "certificate_of_occupancy",
                "notes": f"CO#: {item.get('co', '')} | Type: {item.get('type_of_co', '')}"
            }
            return lead
            
        except Exception as e:
            self.logger.error(f"Error parsing CO record: {e}")
            return None
