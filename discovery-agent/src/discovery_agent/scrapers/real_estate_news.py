import feedparser
import urllib.parse
from datetime import datetime
import logging
import yaml
import os
import re
import time
import json
from openai import OpenAI, AzureOpenAI

class RealEstateDiscovery:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        
        # AI Setup
        self.openai_key = self.config['api_keys'].get('openai_api_key', '')
        self.azure_endpoint = self.config['api_keys'].get('azure_openai_endpoint', '')
        self.azure_deployment = self.config['api_keys'].get('azure_deployment_name', 'gpt-4o-mini')
        self.azure_version = self.config['api_keys'].get('azure_api_version', '2024-02-15-preview')
        
        self.client = None
        
        if self.openai_key and "YOUR_" not in self.openai_key:
            if self.azure_endpoint and "YOUR_" not in self.azure_endpoint:
                # Use Azure OpenAI
                self.logger.info("Initializing Azure OpenAI Client...")
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

        # RSS Feeds
        self.base_google_news_url = "https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en"
        
        self.direct_feeds = [
            "https://www.bizjournals.com/dallas/news/real_estate/commercial/feed",
            "https://www.bisnow.com/rss/dallas-ft-worth",
        ]
        
        self.keywords = [
            "office lease", 
            "relocation", 
            "new headquarters", 
            "office expansion",
            "moving to"
        ]

    def _load_config(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
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
        self.logger.info("Running Real Estate Signal Discovery (RSS + Batch AI)...")
        
        raw_items = []
        
        # 1. Process Google News Feeds
        for keyword in self.keywords:
            # Broader Query: keyword AND (Dallas OR Fort Worth OR DFW)
            query = f'"{keyword}" (Dallas OR "Fort Worth" OR DFW) when:30d'
            encoded_query = urllib.parse.quote(query)
            feed_url = self.base_google_news_url.format(encoded_query)
            
            self.logger.info(f"Fetching RSS for: {keyword}")
            items = self._fetch_feed_items(feed_url, keyword, "google_news_rss")
            raw_items.extend(items)
            time.sleep(1) 
            
        # 2. Process Direct Feeds
        for feed_url in self.direct_feeds:
            self.logger.info(f"Fetching Direct Feed: {feed_url}")
            items = self._fetch_feed_items(feed_url, "Industry News", "industry_rss")
            raw_items.extend(items)
            
        # Deduplicate based on Link URL
        unique_items = {}
        for item in raw_items:
            unique_items[item['link']] = item
            
        unique_list = list(unique_items.values())
        self.logger.info(f"Collected {len(unique_list)} unique raw articles. Starting AI analysis...")
        
        # 3. Batch AI Analysis
        final_leads = self._process_batches(unique_list)
        
        return final_leads

    def _fetch_feed_items(self, feed_url, context, source_type):
        items = []
        try:
            feed = feedparser.parse(feed_url)
            # No pre-filtering here anymore. We capture everything the feed gives us for the AI to decide.
            for entry in feed.entries:
                items.append({
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "published": entry.get('published', datetime.now().strftime("%Y-%m-%d")),
                    "summary": (entry.get('description', '') or entry.get('summary', ''))[:300], # Truncate summary
                    "context": context,
                    "source_type": source_type
                })
        except Exception as e:
            self.logger.error(f"Error parsing feed {feed_url}: {e}")
        return items

    def _process_batches(self, items, batch_size=20):
        if not self.client:
            self.logger.error("No OpenAI Client available for batch processing.")
            return []

        all_leads = []
        
        # Split into chunks
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} items)...")
            
            analyzed_leads = self._analyze_batch(batch)
            all_leads.extend(analyzed_leads)
            
        return all_leads

    def _analyze_batch(self, batch_items):
        # Prepare the prompt input
        items_text = ""
        for idx, item in enumerate(batch_items):
            items_text += f"ITEM {idx}:\nTitle: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"

        prompt = f"""
        You are an Expert Lead Analyst for the Dallas/Fort Worth Commercial Real Estate market.
        Review the following news items and identify ONLY the ones that indicate a VALID commercial office signal.
        
        Criteria for VALID Signal:
        1. Signing a new OFFICE lease (Commercial, not residential/apartment).
        2. Relocating headquarters or office.
        3. Expanding office footprint.
        4. Breaking ground on a new OFFICE building (major tenant named).
        
        Location Constraints:
        - MUST be in the Dallas / Fort Worth Metroplex (Dallas, Fort Worth, Plano, Frisco, Irving, Arlington, Richardson, Southlake, etc.)
        - IGNORE items about properties in Florida, Houston, Austin, New York, etc., unless it involves a MOVE TO Dallas.
        
        Input Items:
        {items_text}
        
        Return a JSON OBJECT with a key "leads" containing a list of valid items.
        Each item in the list should have:
        - original_index: integer (The ITEM number from input)
        - company_name: string (The tenant/company moving)
        - signal_type: string (lease | relocation | expansion | construction)
        - sq_ft: integer (0 if unknown)
        - location: string (Specific City/Area in DFW)
        - reason: string (Why you selected this)
        
        If no items are relevant, return {{"leads": []}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You extract lead data. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            result = json.loads(response.choices[0].message.content)
            valid_indices_list = result.get('leads', [])
            
            # Create a set of valid indices for O(1) lookup
            valid_idx_set = set()
            
            leads = []
            for valid_item in valid_indices_list:
                idx = valid_item.get('original_index')
                if idx is not None and 0 <= idx < len(batch_items):
                    valid_idx_set.add(idx)
                    original = batch_items[idx]
                    
                    self.logger.info(f"✅ AI KEPT: {original['title'][:50]}... | Reason: {valid_item.get('reason', '')}")
                    
                    # Signal Strength Logic
                    signal_strength = "High"
                    if valid_item.get('sq_ft', 0) > 10000:
                        signal_strength = "Very High"

                    lead = {
                        "discovery_date": datetime.now().strftime("%Y-%m-%d"),
                        "company_name": valid_item.get('company_name', 'Unknown'),
                        "domain": "", 
                        "discovery_source": f"rss_{original['source_type']}_ai",
                        "signal_type": valid_item.get('signal_type', 'office_move'),
                        "signal_strength": signal_strength,
                        "signal_date": original['published'],
                        "details": f"AI: {valid_item.get('reason', '')}. SqFt: {valid_item.get('sq_ft', 0)}",
                        "location": valid_item.get('location', "DFW Area"),
                        "timeline": "3-6 Months",
                        "source_url": original['link'],
                        "county": "Dallas/Tarrant/Collin", # Generic for now
                        "all_signals": "real_estate_news",
                        "notes": f"Headline: {original['title']}"
                    }
                    leads.append(lead)
            
            # Log Rejections
            for i, item in enumerate(batch_items):
                if i not in valid_idx_set:
                    self.logger.info(f"❌ AI REJECTED: {item['title'][:50]}...")

            return leads

        except Exception as e:
            self.logger.error(f"Batch AI Analysis Failed: {e}")
            return []
