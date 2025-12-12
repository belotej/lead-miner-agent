import requests
import time
import random
from datetime import datetime
import logging
import yaml
import os
import json
from openai import OpenAI, AzureOpenAI

class JobPostingScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.rapidapi_key = self.config['api_keys'].get('rapidapi_key', '')
        self.base_url = "https://jsearch.p.rapidapi.com/search"

        self.target_titles = self.config['job_posting']['target_titles']
        self.location = "Dallas, TX"

        # AI Setup
        self.openai_key = self.config['api_keys'].get('openai_api_key', '')
        self.azure_endpoint = self.config['api_keys'].get('azure_openai_endpoint', '')
        self.azure_deployment = self.config['api_keys'].get('azure_deployment_name', 'gpt-4o-mini')
        self.azure_version = self.config['api_keys'].get('azure_api_version', '2024-02-15-preview')

        self.client = None

        if self.openai_key and "YOUR_" not in self.openai_key:
            if self.azure_endpoint and "YOUR_" not in self.azure_endpoint:
                # Use Azure OpenAI
                self.logger.info("Initializing Azure OpenAI Client for Job Analysis...")
                self.client = AzureOpenAI(
                    api_key=self.openai_key,
                    api_version=self.azure_version,
                    azure_endpoint=self.azure_endpoint
                )
                self.model_name = self.azure_deployment
            else:
                # Use Standard OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                self.model_name = "gpt-4o-mini"
        else:
            self.logger.warning("OpenAI API Key not found. AI filtering disabled.")

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
        raw_leads = []

        if not self.rapidapi_key or self.rapidapi_key == "YOUR_RAPIDAPI_KEY":
            self.logger.error("RapidAPI key not configured in config.yaml")
            return []

        for title in self.target_titles:
            self.logger.info(f"Searching for title: {title}")
            leads = self.search_jsearch(title)
            raw_leads.extend(leads)
            # Be polite
            time.sleep(2)

        self.logger.info(f"Collected {len(raw_leads)} raw job leads. Starting AI analysis...")

        # Run AI Analysis
        final_leads = self._process_batches(raw_leads)
        return final_leads

    def _process_batches(self, leads, batch_size=10):
        if not self.client:
            return leads # Return raw if no AI

        final_leads = []
        for i in range(0, len(leads), batch_size):
            batch = leads[i:i + batch_size]
            self.logger.info(f"Processing job batch {i//batch_size + 1} ({len(batch)} items)...")
            analyzed_leads = self._analyze_batch(batch)
            final_leads.extend(analyzed_leads)

        return final_leads

    def _analyze_batch(self, batch_leads):
        items_text = ""
        for idx, lead in enumerate(batch_leads):
            desc = lead.get('full_description', '')[:1000] # Limit to 1000 chars to save tokens
            items_text += f"ITEM {idx}:\nTitle: {lead['headline']}\nCompany: {lead['company_name']}\nDescription: {desc}\n\n"

        prompt = f"""
        You are an Expert in Commercial Office Procurement and Facilities Management.
        Analyze job postings to identify roles that have AUTHORITY or INFLUENCE over buying OFFICE FURNITURE or managing OFFICE MOVES/BUILD-OUTS.

        POSITIVE Signals (High Confidence - 70-100):
        - Explicit: "Vendor management" for facilities/services, "Office relocation", "Move management"
        - Explicit: "Procurement of FF&E" (Furniture, Fixtures, Equipment), "Furniture procurement"
        - Explicit: "Workspace strategy", "Workplace experience", "Space planning"
        - Explicit: "Capital projects", "Facilities budget management", "Office build-out"
        - Implied: "Facilities Manager/Director" at a corporate office
        - Implied: "Office Manager" (often handles furniture/supplies purchasing)
        - Implied: "Workplace Manager", "Real Estate Manager" at corporations

        NEGATIVE Signals (Low Confidence - Below 50):
        - "Apartment", "Residential", "Multi-family", "Property Management" (residential real estate)
        - "Maintenance Technician", "Janitor", "Groundskeeper" (maintenance, not purchasing)
        - "Hospital", "Medical Center", "Healthcare" facilities management (different buyer)
        - "Hotel", "Hospitality", "Restaurant" facilities (not office furniture)
        - "Retail Store Manager" (not office furniture buyer)
        - "IT Manager" without office buildout context
        - "Receptionist", "Administrative Assistant" (no budget authority)

        Items to Analyze:
        {items_text}

        Return a JSON OBJECT with a key "analyses" containing a list for each item:
        - original_index: integer
        - confidence: integer (0-100)
          - 80-100: Explicit mention of furniture, moves, or procurement authority
          - 50-79: Facilities/Office Manager role that implies purchasing authority
          - Below 50: Residential, Healthcare, Hospitality, Maintenance, or unrelated
        - signal_strength: "High", "Medium", "Low"
        - industry: string (e.g. "Technology", "Financial Services", "Professional Services", "Healthcare", "Hospitality", "Residential Real Estate")
        - role_level: string ("Executive", "Director", "Manager", "Coordinator", "Entry-Level")
        - reasoning: Brief explanation of why this role does or doesn't buy furniture

        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You analyze job roles for procurement authority. Return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            result = json.loads(response.choices[0].message.content)
            analyses = result.get('analyses', [])

            # Map results back to leads
            for analysis in analyses:
                idx = analysis.get('original_index')
                if idx is not None and 0 <= idx < len(batch_leads):
                    lead = batch_leads[idx]
                    lead['confidence'] = analysis.get('confidence', 50)
                    lead['reasoning'] = analysis.get('reasoning', 'AI Analysis Failed')
                    lead['signal_strength'] = analysis.get('signal_strength', 'Medium')
                    lead['industry'] = analysis.get('industry', 'Unknown')
                    lead['role_level'] = analysis.get('role_level', 'Unknown')

                    # Build rich details string
                    industry = lead['industry']
                    role_level = lead['role_level']
                    reasoning = lead['reasoning']
                    headline = lead.get('headline', 'Unknown Role')

                    details_parts = [f"Role: {headline}"]
                    details_parts.append(f"Level: {role_level}")
                    details_parts.append(f"Industry: {industry}")
                    details_parts.append(f"AI: {reasoning}")
                    lead['details'] = ". ".join(details_parts)

            # Filter and Return (Threshold: 50)
            valid_leads = []
            for lead in batch_leads:
                if lead.get('confidence', 0) >= 50:
                    valid_leads.append(lead)
                    if lead.get('confidence', 0) > 70:
                        self.logger.info(f"[ACCEPTED] {lead['headline']} | Conf: {lead['confidence']} | Industry: {lead.get('industry', 'Unknown')}")
                    else:
                        self.logger.info(f"[KEPT MARGINAL] {lead['headline']} | Conf: {lead['confidence']} | Industry: {lead.get('industry', 'Unknown')}")
                else:
                    self.logger.info(f"[REJECTED] {lead['headline']} | Conf: {lead['confidence']} | Industry: {lead.get('industry', 'Unknown')}")

            return valid_leads

        except Exception as e:
            self.logger.error(f"Batch AI Analysis Failed: {e}")
            return batch_leads # Return original if AI fails

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
                "confidence": 80,
                "signal_date": posted_date,
                "headline": job_title,
                "summary": f"Hiring for {job_title} in {location}",
                "reasoning": f"Job posting for {job_title} indicates potential facilities needs.",
                "full_description": job_description, # For AI Analysis
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
