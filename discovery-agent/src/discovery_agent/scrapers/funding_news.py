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

class FundingNewsDiscovery:
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
                self.logger.info("Initializing Azure OpenAI Client for Funding News...")
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
        
        # Direct Tech/Funding Feeds
        self.direct_feeds = [
            "https://dallasinnovates.com/feed/", # Excellent for local funding
            "https://techcrunch.com/feed/",      # National, needs filtering
            "https://feeds.feedburner.com/venturebeat/SZYF" # VentureBeat
        ]
        
        # Funding Specific Queries
        # Focus on Dallas/DFW explicitly
        cities = "Dallas OR Plano OR Frisco OR Irving OR Richardson OR Addison"
        regional = "DFW OR \"Dallas-Fort Worth\""
        
        self.google_queries = [
            # 1. Venture Capital Rounds
            f'("raised" OR "funding" OR "investment") ("Series A" OR "Series B" OR "Series C") ({cities} OR {regional})',
            
            # 2. Private Equity / Acquisitions (often lead to consolidation/moves)
            f'("acquired by" OR "private equity") ({cities} OR {regional}) -real estate -multifamily',
            
            # 3. Generic Funding keywords with million dollar threshold
            f'("million" OR "M") ("capital raise" OR "venture capital") ({cities}) -charity -donation'
        ]
        
        # Strict Client-Side Location Filter (Same as Real Estate)
        self.target_locations = [
            "dallas", "fort worth", "dfw", "metroplex", "arlington", "plano", "garland", 
            "irving", "mckinney", "frisco", "grand prairie", "mesquite", "denton", 
            "richardson", "lewisville", "addison", "allen", "southlake", "grapevine", 
            "coppell", "rockwall", "carrollton", "farmers branch", "the colony", 
            "flower mound", "keller"
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
        self.logger.info("Running Funding News Discovery...")
        
        raw_items = []
        
        # 1. Process Google News Feeds
        for idx, query_template in enumerate(self.google_queries):
            query = f'{query_template} when:7d'
            encoded_query = urllib.parse.quote(query)
            feed_url = self.base_google_news_url.format(encoded_query)
            
            self.logger.info(f"Fetching Funding RSS for Query #{idx+1}")
            items = self._fetch_feed_items(feed_url, query_template, f"funding_google_q{idx+1}")
            raw_items.extend(items)
            time.sleep(1) 
            
        # 2. Process Direct Feeds
        for feed_url in self.direct_feeds:
            self.logger.info(f"Fetching Direct Feed: {feed_url}")
            
            source_name = "direct_unknown"
            if "dallasinnovates" in feed_url:
                source_name = "direct_dallas_innovates"
            elif "techcrunch" in feed_url:
                source_name = "direct_techcrunch"
            elif "venturebeat" in feed_url:
                source_name = "direct_venturebeat"
                
            items = self._fetch_feed_items(feed_url, "Tech News", source_name)
            raw_items.extend(items)
            
        # Deduplicate
        unique_items = {}
        for item in raw_items:
            unique_items[item['link']] = item
        unique_list = list(unique_items.values())
        
        self.logger.info(f"Collected {len(unique_list)} unique funding articles. Starting AI analysis...")
        
        # DEBUG LOG
        self._save_raw_audit_log(unique_list)

        # 3. Batch AI Analysis
        final_leads = self._process_batches(unique_list)
        
        return final_leads

    def _save_raw_audit_log(self, items):
        import pandas as pd
        try:
            # Resolve absolute path to data directory
            current_dir = os.path.dirname(os.path.abspath(__file__)) 
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) 
            data_dir = os.path.join(root_dir, "data")
            
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            df = pd.DataFrame(items)
            # Select useful columns
            cols = ['title', 'source_type', 'published', 'link', 'summary']
            df = df[cols] if set(cols).issubset(df.columns) else df
            
            output_path = os.path.join(data_dir, "debug_funding_rss_log.csv")
            
            if os.path.exists(output_path):
                df.to_csv(output_path, mode='a', header=False, index=False)
            else:
                df.to_csv(output_path, index=False)
        except Exception as e:
            self.logger.warning(f"Failed to save audit log: {e}")

    def _fetch_feed_items(self, feed_url, context, source_type):
        import requests
        items = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(feed_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
                
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                raw_summary = entry.get('description', '') or entry.get('summary', '')
                clean_summary = raw_summary
                if raw_summary:
                    try:
                        soup = BeautifulSoup(raw_summary, "html.parser")
                        clean_summary = soup.get_text(separator=" ", strip=True)
                    except Exception:
                        pass
                
                # STRICT LOCATION FILTER (Client-Side)
                # Apply to Google News AND National feeds (TechCrunch)
                # Only Dallas Innovates is safe to skip this
                if "dallasinnovates" not in source_type:
                    content_text = (entry.get('title', '') + " " + clean_summary)
                    if not self._is_location_relevant(content_text):
                        continue

                items.append({
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "published": entry.get('published', datetime.now().strftime("%Y-%m-%d")),
                    "summary": clean_summary[:500],
                    "context": context,
                    "source_type": source_type
                })
        except Exception as e:
            self.logger.error(f"Error parsing feed {feed_url}: {e}")
        return items

    def _process_batches(self, items, batch_size=20):
        if not self.client:
            return []
            
        final_leads = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.logger.info(f"Processing funding batch {i//batch_size + 1} ({len(batch)} items)...")
            analyzed_leads = self._analyze_batch(batch)
            final_leads.extend(analyzed_leads)
            
        return final_leads

    def _analyze_batch(self, batch_items):
        items_text = ""
        for idx, item in enumerate(batch_items):
            items_text += f"ITEM {idx}:\nTitle: {item['title']}\nSummary: {item['summary']}\nLink: {item['link']}\n\n"
            
        prompt = f"""
        You are an Expert Funding Analyst identifying companies that recently raised capital in Dallas/Fort Worth.
        These companies are likely to expand their offices and need furniture.

        Review the following news items and identify ONLY valid funding events.

        VALID Funding Signals:
        - Series A, B, C, D funding rounds
        - Seed funding or Venture Capital investment
        - Private Equity investment (growth equity, not buyouts)
        - The company receiving funds MUST be headquartered in Dallas/Fort Worth/DFW Metroplex

        EXCLUDE (Not Valid):
        - M&A where the company is being ACQUIRED/SOLD (unless explicitly mentions expansion)
        - Real Estate investment funds or REITs
        - Stock market news (IPO filings without funding context)
        - Restaurant/Hospitality businesses (not our target market)
        - Healthcare/Medical practices (not our target market)
        - Charitable donations or grants
        - The investor being from DFW (we want the COMPANY to be in DFW)

        Items to Analyze:
        {items_text}

        Return a JSON OBJECT with a key "leads" containing a list of valid items.
        Each item in the list should have:
        - original_index: integer
        - company_name: string (The company RAISING the money)
        - funding_amount: string (e.g. "$15M", "Undisclosed")
        - round_type: string (Series A, Seed, Growth Equity, etc.)
        - industry: string (e.g. "SaaS", "FinTech", "Professional Services", "Manufacturing")
        - location: string (Specific city in DFW)
        - company_website: string (if mentioned, otherwise "Unknown")
        - reason: string (Brief explanation of why this is a valid lead)

        If no items are relevant, return {{"leads": []}}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You extract funding data. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            result = json.loads(response.choices[0].message.content)
            valid_indices_list = result.get('leads', [])
            
            leads = []
            for valid_item in valid_indices_list:
                idx = valid_item.get('original_index')
                if idx is not None and 0 <= idx < len(batch_items):
                    original = batch_items[idx]
                    
                    # Signal Strength: >$10M is Very High
                    amount_str = valid_item.get('funding_amount', '0')
                    signal_strength = "High"
                    if "M" in amount_str or "B" in amount_str:
                         # Basic heuristic: if double digit millions
                         if any(c in amount_str for c in ['1','2','3','4','5','6','7','8','9']):
                             signal_strength = "Very High"

                    # Extract new fields
                    industry = valid_item.get('industry', 'Unknown')
                    company_website = valid_item.get('company_website', 'Unknown')
                    funding_amount = valid_item.get('funding_amount', 'Undisclosed')
                    round_type = valid_item.get('round_type', 'Unknown')
                    reason = valid_item.get('reason', '')

                    # Build rich details string
                    details = f"Raised {funding_amount} ({round_type}). Industry: {industry}."
                    if company_website and company_website != "Unknown":
                        details += f" Website: {company_website}."
                    details += f" AI: {reason}"

                    lead = {
                        "discovery_date": datetime.now().strftime("%Y-%m-%d"),
                        "company_name": valid_item.get('company_name', 'Unknown'),
                        "domain": company_website if company_website != "Unknown" else "",
                        "discovery_source": f"funding_{original['source_type']}",
                        "signal_type": "funding_round",
                        "signal_strength": signal_strength,
                        "signal_date": original['published'],
                        "details": details,
                        "location": valid_item.get('location', "DFW Area"),
                        "timeline": "Immediate (Hiring)",
                        "source_url": original['link'],
                        "county": "Dallas/Collin",
                        "all_signals": "funding_news",
                        "notes": f"Headline: {original['title']}\nSummary: {original['summary']}"
                    }
                    leads.append(lead)
                    self.logger.info(f"[FUNDING] {lead['company_name']} - {lead['details']}")

            return leads

        except Exception as e:
            self.logger.error(f"Batch AI Analysis Failed: {e}")
            return []
