# Discovery Agent - Logic & Architecture

## Overview
The Discovery Agent is the "Sensor" of the Lead Mining System. Its purpose is to scan the internet for "Buying Signals" that indicate a company is expanding, relocating, or returning to office in the Dallas/Fort Worth (DFW) area.

## Architecture
The agent consists of 3 primary scrapers running sequentially:
1.  **Job Posting Scraper** (`job_postings.py`)
2.  **Real Estate News Scraper** (`real_estate_news.py`)
3.  **Funding News Scraper** (`funding_news.py`)

All leads are aggregated, deduplicated, and saved to `data/leads_repository.xlsx`.

---

## 1. Job Posting Scraper
**Goal**: Identify companies hiring for roles that manage physical office space.

*   **Source**: JSearch API (RapidAPI), which aggregates Indeed, LinkedIn, Glassdoor, Google Jobs.
*   **Trigger Titles**:
    *   "Facilities Manager"
    *   "Director of Facilities"
    *   "VP Real Estate"
    *   "Office Manager"
    *   "Workplace Manager"
*   **Logic**:
    *   Queries API for `{Title} in Dallas, TX`.
    *   Filters for postings posted in the last **7 days**.
    *   Extracts Company Name and Job Title.
*   **Output Signal**: `hiring_trigger_role` (High Intent).

---

## 2. Real Estate News Scraper
**Goal**: Find confirmed lease signings, relocations, expansions, and Return-to-Office (RTO) mandates.

*   **Sources**:
    *   **Google News RSS**: 7 Advanced Queries (see below).
    *   **Direct Feeds**:
        *   Dallas Business Journal (Commercial RE Channel)
        *   Bisnow DFW
        *   Dallas Innovates
        *   Fort Worth Business Press
*   **Advanced Google Queries (7-Day Lookback)**:
    1.  **Leases**: `"office lease" ({DFW Cities}) ("square feet" OR sqft) -apartment -residential`
    2.  **Relocations**: `("headquarters" OR "corporate headquarters") (moving OR relocating) ({DFW}) -personal`
    3.  **New Offices**: `("new office" OR "opening office") ({DFW}) (company OR firm) employees`
    4.  **Expansions**: `("office expansion" OR "expanding operations") ({DFW}) (employees OR hiring)`
    5.  **Signed Deals**: `("signed lease" OR "leased") office ({DFW}) "square feet"`
    6.  **Buildouts**: `("corporate campus" OR "office buildout") ({DFW})`
    7.  **RTO**: `("return to office" OR "RTO" OR "office mandate") ({DFW}) (days a week OR hybrid)`
*   **Filtering Logic**:
    1.  **Strict Location**: Client-side check against 40+ DFW cities (e.g. Plano, Frisco, Addison). Discards anything not matching.
    2.  **Deduplication**:
        *   **URL**: Remove exact duplicates.
        *   **Title**: Fuzzy match (Similarity > 85%) to remove syndicated stories.
    3.  **AI Analysis (Azure OpenAI GPT-4o)**:
        *   Prompt: *"Identify VALID commercial office signals... Ignore apartments/retail... DEDUPLICATE events."*
        *   Extracts: Company Name, Square Footage, Signal Type (Lease vs RTO).

---

## 3. Funding News Scraper
**Goal**: Find startups raising Capital (Series A/B/C) which triggers headcount growth.

*   **Sources**:
    *   **Google News RSS**: `("raised" OR "funding") ("Series A" OR "Series B") ({DFW})`.
    *   **Direct Feeds**: Dallas Innovates, TechCrunch, VentureBeat.
*   **Logic**:
    *   Similar strict location filtering (discard non-DFW news).
    *   **AI Analysis**:
        *   Prompt: *"Identify companies raising >$10M capital in DFW."*
        *   Strength: >$10M = "Very High" signal.

---

## Configuration
*   **Config File**: `discovery-agent/config/config.yaml`
*   **Secrets**: Azure API Key, RapidAPI Key (Excluded from Git).
*   **Outputs**:
    *   `leads_repository.xlsx`: Final actionable list.
    *   `debug_raw_rss_log.csv`: Audit trail of all raw RSS items before filtering.
