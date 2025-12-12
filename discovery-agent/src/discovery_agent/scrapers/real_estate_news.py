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
from bs4 import BeautifulSoup
from discovery_agent.utils.deduplication import Deduplication

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
            "https://rss.bizjournals.com/feed/225b05c17d74d990c84b5a662dbead1d328d16cf/14001?market=dallas&selectortype=channel&selectorvalue=1,2,3,4,5,9,7,15",
            "https://www.bisnow.com/rss/dallas-ft-worth",
            "https://fortworthbusiness.com/feed/",
            "https://dallasinnovates.com/feed/"
        ]
        
        # Advanced Google News Queries
        # Core cities for most queries
        core_cities = "Dallas OR Plano OR Frisco OR Irving"
        # Extended cities for some queries
        extended_cities = "Dallas OR \"Fort Worth\" OR Plano OR Frisco OR Irving OR Southlake OR Allen"
        # Regional catch-all
        regional = "DFW OR \"Dallas-Fort Worth\""

        self.google_queries = [
            # 1. Leases with SqFt requirement (Filters out residential)
            f'"office lease" ({extended_cities}) ("square feet" OR sqft) -apartment -residential',
            
            # 2. HQ Relocations (High Value)
            f'("headquarters" OR "corporate headquarters") (moving OR relocating) ({regional} OR {core_cities}) -personal',
            
            # 3. New Offices with employee context
            f'("new office" OR "opening office") ({core_cities} OR Southlake OR Allen) (company OR firm) employees',
            
            # 4. Expansions with hiring context
            f'("office expansion" OR "expanding operations") ({regional} OR {extended_cities}) (employees OR hiring)',
            
            # 5. Explicit signed leases
            f'("signed lease" OR "leased") office ({core_cities}) "square feet"',
            
            # 6. Buildouts / Campuses
            f'("corporate campus" OR "office buildout") ({regional} OR {extended_cities})',
            
            # 7. Return to Office (RTO) Mandates
            f'("return to office" OR "RTO" OR "office mandate") ({regional} OR {extended_cities}) (days a week OR hybrid OR "in-person")'
        ]
        
        # Strict Client-Side Location Filter
        self.target_locations = [
            "dallas", "fort worth", "dfw", "metroplex", "arlington", "plano", "garland", 
            "irving", "mckinney", "frisco", "grand prairie", "mesquite", "denton", 
            "richardson", "lewisville", "addison", "allen", "southlake", "grapevine", 
            "coppell", "rockwall", "carrollton", "farmers branch", "the colony", 
            "flower mound", "keller", "burleson", "mansfield", "north richland hills", 
            "euless", "bedford", "hurst", "lancaster", "desoto", "cedar hill", 
            "las colinas", "legacy west", "uptown", "deep ellum", "bishop arts"
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
            
    def _is_location_relevant(self, text):
        """Check if text contains any of the target DFW locations."""
        text_lower = text.lower()
        return any(loc in text_lower for loc in self.target_locations)

    def run(self):
        self.logger.info("Running Real Estate Signal Discovery (RSS + Batch AI)...")
        
        raw_items = []
        
        # 1. Process Google News Feeds (Advanced Queries)
        for idx, query_template in enumerate(self.google_queries):
            # Append time filter
            query = f'{query_template} when:7d'
            encoded_query = urllib.parse.quote(query)
            feed_url = self.base_google_news_url.format(encoded_query)
            
            self.logger.info(f"Fetching RSS for Query #{idx+1}")
            # Source name: google_news_q1, q2, etc.
            items = self._fetch_feed_items(feed_url, query_template, f"google_news_q{idx+1}")
            raw_items.extend(items)
            time.sleep(1) 
            
        # 2. Process Direct Feeds
        for feed_url in self.direct_feeds:
            self.logger.info(f"Fetching Direct Feed: {feed_url}")
            
            # Better Source Naming
            source_name = "direct_unknown"
            if "bizjournals" in feed_url:
                source_name = "direct_bizjournals"
            elif "dallasinnovates" in feed_url:
                source_name = "direct_dallas_innovates"
            elif "fortworthbusiness" in feed_url:
                source_name = "direct_fw_business_press"
            elif "bisnow" in feed_url:
                source_name = "direct_bisnow"
            else:
                # Fallback: extraction
                domain = urllib.parse.urlparse(feed_url).netloc.replace("www.", "").split(".")[0]
                source_name = f"direct_{domain}"

            items = self._fetch_feed_items(feed_url, "Industry News", source_name)
            raw_items.extend(items)
            
        # Deduplicate based on Link URL
        unique_items = {}
        for item in raw_items:
            unique_items[item['link']] = item
            
        unique_list = list(unique_items.values())
        self.logger.info(f"Collected {len(unique_list)} items (unique links).")

        # Deduplicate based on Title Similarity (Fuzzy Match)
        deduplicator = Deduplication()
        final_unique_list = deduplicator.deduplicate_raw_items(unique_list)
        self.logger.info(f"After title deduplication: {len(final_unique_list)} items.")
        
        # DEBUG: Save Raw Items to CSV for Audit
        self._save_raw_audit_log(final_unique_list)
        
        # 3. Batch AI Analysis
        self.logger.info("Starting AI analysis...")
        final_leads = self._process_batches(final_unique_list)
        
        return final_leads

    def _save_raw_audit_log(self, items):
        import pandas as pd
        try:
            # Resolve absolute path to data directory
            current_dir = os.path.dirname(os.path.abspath(__file__)) # src/discovery_agent/scrapers
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # discovery-agent
            data_dir = os.path.join(root_dir, "data")
            
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            df = pd.DataFrame(items)
            # Select useful columns
            cols = ['title', 'source_type', 'published', 'link', 'summary']
            df = df[cols] if set(cols).issubset(df.columns) else df
            
            output_path = os.path.join(data_dir, "debug_raw_rss_log.csv")
            
            # Append if exists, or create new
            if os.path.exists(output_path):
                df.to_csv(output_path, mode='a', header=False, index=False)
            else:
                df.to_csv(output_path, index=False)
            self.logger.info(f"Saved raw audit log to {output_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save audit log: {e}")

    def _fetch_feed_items(self, feed_url, context, source_type):
        import requests
        items = []
        try:
            # Use requests with User-Agent to bypass 403 Forbidden blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(feed_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch feed {feed_url}: Status {response.status_code}")
                return []
                
            # Parse the XML content string
            feed = feedparser.parse(response.content)
            
            # No pre-filtering here anymore. We capture everything the feed gives us for the AI to decide.
            for entry in feed.entries:
                raw_summary = entry.get('description', '') or entry.get('summary', '')
                
                # Clean HTML
                clean_summary = raw_summary
                if raw_summary:
                    try:
                        soup = BeautifulSoup(raw_summary, "html.parser")
                        clean_summary = soup.get_text(separator=" ", strip=True)
                    except Exception:
                        pass # Fallback to raw if BS4 fails
                
                # STRICT LOCATION FILTER (Client-Side)
                # Only apply to Google News results, as Direct Feeds are already curated
                if source_type.startswith("google_news"):
                    content_text = (entry.get('title', '') + " " + clean_summary)
                    if not self._is_location_relevant(content_text):
                        continue

                items.append({
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "published": entry.get('published', datetime.now().strftime("%Y-%m-%d")),
                    "summary": clean_summary[:500], # Clean text, then limit to 500 chars
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
        You are identifying companies that will need OFFICE FURNITURE due to moves, expansions, or office changes.

        Review the following news items and identify ONLY valid commercial office signals.

        VALID Signals (These companies will likely need furniture):
        1. Signing a new OFFICE lease (or renewing/expanding existing lease)
        2. Relocating headquarters or opening a new regional office
        3. Breaking ground on or completing a new corporate campus/office building
        4. Mandating "Return to Office" (RTO) for employees (especially 4-5 days/week)
        5. Major office renovation or build-out

        IMPORTANT - EXCLUDE These (Not Valid Leads):
        - Residential/Apartment/Multi-family news (CRITICAL - these are NOT office)
        - Retail/Restaurant leases (not office furniture buyers)
        - Industrial/Warehouse leases (not office furniture buyers)
        - Real estate brokerages or landlords as the "company" (they broker deals, they don't buy furniture)
        - General market reports without a specific TENANT/COMPANY name
        - "Top Brokers" lists, awards, or opinion pieces
        - News about a building being SOLD (unless a new tenant is named)

        DEDUPLICATION:
        - If multiple items refer to the SAME event/company, return ONLY ONE lead (the most detailed one)

        Items to Analyze:
        {items_text}

        Return a JSON OBJECT with a key "leads" containing a list of valid items.
        Each item in the list should have:
        - original_index: integer (The ITEM number from input)
        - company_name: string (The TENANT/COMPANY moving - NOT the landlord or broker)
        - signal_type: string (lease | relocation | expansion | construction | rto | renovation)
        - sq_ft: integer (0 if unknown)
        - location: string (Specific City/Area in DFW)
        - timeline: string (e.g. "Q1 2025", "Summer 2025", "Immediate", "Unknown")
        - industry: string (e.g. "Technology", "Financial Services", "Law Firm", "Professional Services")
        - reason: string (Brief explanation of why this company needs furniture)

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
                    
                    self.logger.info(f"[KEPT] {original['title'][:50]}... | Reason: {valid_item.get('reason', '')}")

                    # Extract new fields
                    sq_ft = valid_item.get('sq_ft', 0)
                    timeline = valid_item.get('timeline', 'Unknown')
                    industry = valid_item.get('industry', 'Unknown')
                    signal_type = valid_item.get('signal_type', 'office_move')
                    reason = valid_item.get('reason', '')

                    # Signal Strength Logic
                    signal_strength = "High"
                    if sq_ft > 10000:
                        signal_strength = "Very High"
                    elif signal_type == "rto":
                        signal_strength = "Very High"  # RTO mandates are strong signals

                    # Build rich details string
                    details_parts = [f"Signal: {signal_type.upper()}"]
                    if sq_ft > 0:
                        details_parts.append(f"Size: {sq_ft:,} sqft")
                    details_parts.append(f"Industry: {industry}")
                    if timeline != "Unknown":
                        details_parts.append(f"Timeline: {timeline}")
                    details_parts.append(f"AI: {reason}")
                    details = ". ".join(details_parts)

                    lead = {
                        "discovery_date": datetime.now().strftime("%Y-%m-%d"),
                        "company_name": valid_item.get('company_name', 'Unknown'),
                        "domain": "",
                        "discovery_source": f"rss_{original['source_type']}_ai",
                        "signal_type": signal_type,
                        "signal_strength": signal_strength,
                        "signal_date": original['published'],
                        "details": details,
                        "location": valid_item.get('location', "DFW Area"),
                        "timeline": timeline,
                        "source_url": original['link'],
                        "county": "Dallas/Tarrant/Collin",
                        "all_signals": "real_estate_news",
                        "notes": f"Headline: {original['title']}\nSummary: {original['summary']}"
                    }
                    leads.append(lead)
            
            # Log Rejections
            for i, item in enumerate(batch_items):
                if i not in valid_idx_set:
                    self.logger.info(f"[REJECTED] {item['title'][:50]}...")

            return leads

        except Exception as e:
            self.logger.error(f"Batch AI Analysis Failed: {e}")
            return []
