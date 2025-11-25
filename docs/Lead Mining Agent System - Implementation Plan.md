# Lead Mining Agent System - Implementation Plan
## Starting with Discovery Agent (DFW Area)

---

## Executive Summary

This document outlines the implementation plan for an AI-powered **Lead Mining Agent System** designed to identify, enrich, qualify, and present high-quality sales leads to Vari's SDR team. The system replaces expensive third-party intent data subscriptions (like ZoomInfo) with an independent, ethical, low-cost solution built on public records, job postings, and news monitoring.

The system consists of three specialized agents working in sequence, but **this document focuses on Phase 1: Building the Discovery Agent for the DFW market.**

---

## Three-Agent Architecture

### Agent 1: Discovery Agent (THIS DOCUMENT - Phase 1)
**Purpose**: Identify companies showing concrete buying signals ("hard signals") based on verifiable trigger events.

**Outputs**: Raw list of companies with trigger events (job postings, funding, office moves, construction permits)

**Phase 1 Focus**: DFW area using five ethical, low/no-cost data sources

**Timeline**: Weeks 1-4

---

### Agent 2: Enrichment Agent (Phase 2 - Future Document)
**Purpose**: Enrich discovered companies with firmographic, technographic, and contextual data to support qualification and outreach.

**Data Sources** (planned):
- Free/freemium APIs (Clearbit, Hunter.io, Crunchbase)
- Company website scraping
- LinkedIn company pages (public data only)
- Google News API for recent company news
- Public business registries

**Outputs**: Enriched company profiles with:
- Industry, employee count, revenue estimates
- Funding history
- Key contacts (names, titles, LinkedIn profiles)
- Recent news and context
- Office locations

**Timeline**: Weeks 5-7 (after Discovery Agent is operational)

---

### Agent 3: Qualification Agent (Phase 3 - Future Document)
**Purpose**: Score and rank enriched leads based on Ideal Customer Profile (ICP) fit and buying signal strength.

**Scoring Model**:
- **50 points**: Hard buying signals (job postings, funding, real estate news, public records)
- **30 points**: Firmographic fit (size, industry, revenue)
- **20 points**: Growth and timing signals

**Outputs**: 
- Scored leads with priority tiers (Hot/Warm/Cold)
- Lead briefs with outreach strategy for SDR team
- Daily email digest of top leads
- Excel repository with all lead data

**Timeline**: Weeks 8-10 (after Enrichment Agent is operational)

---

## System Data Flow

```
Discovery Agent → Raw Leads (companies with trigger events)
                        ↓
Enrichment Agent → Enriched Leads (with firmographic data, contacts, news)
                        ↓
Qualification Agent → Scored Leads (with priority ranking)
                        ↓
Lead Briefs → SDR Team (daily email with actionable leads)
                        ↓
(Future) Salesforce Integration → Auto-create leads for hot prospects
```

---

## Why Start with Discovery Agent?

The Discovery Agent is the foundation of the entire system. Without high-quality lead discovery, enrichment and scoring don't matter. By focusing on the Discovery Agent first:

1. **Validate the approach** - Prove we can find quality leads without expensive subscriptions
2. **Build incrementally** - Get something working quickly, then expand
3. **Learn and iterate** - Understand what signals work best before investing in enrichment
4. **Demonstrate value** - Show stakeholders real companies with real buying signals
5. **Test DFW first** - Prove the model in one market before scaling

**Success Criteria for Discovery Agent**: 
- Discover 30-60 DFW companies per week showing strong buying signals
- 70%+ match Vari's ICP (50-999 employees, target industries)
- Provide actionable context (what triggered the discovery, timeline, location)

Once the Discovery Agent proves successful in DFW, we'll:
- Build the Enrichment Agent (Weeks 5-7)
- Build the Qualification Agent (Weeks 8-10)
- Expand geography (Austin, Houston, San Antonio)
- Add more sophisticated signals and automation

---

## Discovery Agent - DFW Area Implementation Plan

### Overview

This section outlines the detailed implementation plan for the **Discovery Agent** that identifies companies in the Dallas-Fort Worth (DFW) area showing strong buying signals for office furniture, using only ethical, low-cost or free data sources.

**Geographic Focus**: DFW Metroplex (Phase 1)  
**Timeline**: 4 weeks to operational  
**Cost**: $0-50/month  
**Expected Output**: 30-60 qualified companies per week

## Geographic Scope

**Phase 1 Target Area: DFW Metroplex**
- Dallas County
- Tarrant County (Fort Worth)
- Collin County (Plano, Frisco, McKinney)
- Denton County

**Future Expansion**: Austin, Houston, San Antonio (Phase 2)

---

## Discovery Signal Sources

### 1. Job Postings

#### Why This Signal Matters
Companies hiring for facilities, operations, or workplace management roles are actively preparing for office changes, growth, or improvements.

#### Target Job Titles
- Facilities Manager
- Director of Facilities
- VP of Real Estate / Corporate Real Estate
- Office Manager
- Workplace Manager
- Director of Operations (when facilities-related)
- Space Planning Manager
- Workplace Experience Manager

#### Data Sources

**Indeed (Scraping-Friendly with Rate Limits)**
- **URL Pattern**: `https://www.indeed.com/jobs?q=[job_title]&l=Dallas%2C+TX`
- **Terms**: Indeed allows reasonable scraping per their robots.txt
- **Rate Limit**: 1-2 requests per second maximum
- **Data Available**:
  - Company name
  - Job title
  - Location
  - Posting date
  - Job description (can indicate office size/project)
  
**Implementation Approach**:
```python
# Use requests + BeautifulSoup or Playwright for JavaScript-heavy pages
# Respect robots.txt
# Add delays between requests (1-2 seconds minimum)
# Rotate user agents
# Filter by "Dallas, TX" or "DFW" location
```

**Glassdoor (Limited)**
- Similar to Indeed
- Check robots.txt for current policy
- May require more careful rate limiting

**Direct Company Career Pages**
- Once companies are identified from other signals, check their career pages
- Most companies allow automated access to career pages
- No rate limit concerns for occasional checks

#### Output Schema
```json
{
  "source": "job_posting",
  "company_name": "string",
  "job_title": "string",
  "posting_date": "YYYY-MM-DD",
  "location": "city, state",
  "job_url": "string",
  "description_snippet": "string (first 200 chars)",
  "seniority_level": "entry|mid|senior|executive",
  "discovery_date": "YYYY-MM-DD",
  "signal_strength": "high|medium|low"
}
```

**Signal Strength Scoring**:
- **High**: Facilities Manager, VP Real Estate, Director of Facilities
- **Medium**: Office Manager, Workplace Manager
- **Low**: General operations roles

---

### 2. Funding Announcements

#### Why This Signal Matters
Companies that recently raised Series B+ funding often invest in office infrastructure, expansion, and employee experience.

#### Data Sources

**Crunchbase (Free Tier + Web Scraping)**
- **Free Tier**: 5 API calls per minute, limited data
- **Web Access**: Can view public company profiles
- **Scraping Approach**: 
  - Search for DFW-based companies
  - Filter by recent funding (last 90 days)
  - Series B or later, $10M+ preferred
  
**URL Pattern**: `https://www.crunchbase.com/discover/organization.companies/[filters]`

**Dallas Business Journal & Fort Worth Business Press**
- Local business news sources
- Often announce local funding rounds
- **Access**: 
  - Free articles available
  - RSS feeds
  - Web scraping of public articles

**TechCrunch, VentureBeat (National Tech News)**
- Filter for DFW-based companies
- RSS feeds available
- API access available (some free tiers)

**Google News API**
- Search query: `"Series B" OR "Series C" OR "funding" AND (Dallas OR "Fort Worth" OR DFW OR Plano OR Frisco)`
- Free tier: 100 requests/day
- Filter by publication date (last 90 days)

**DFW-Specific Tech/Startup Publications**
- Built In Austin (covers Texas tech scene)
- Dallas Innovates
- RSS feeds and web scraping

#### Output Schema
```json
{
  "source": "funding",
  "company_name": "string",
  "funding_round": "Series A|B|C|D|...",
  "funding_amount": "integer (in millions)",
  "announcement_date": "YYYY-MM-DD",
  "investors": ["array of investor names"],
  "news_source": "string",
  "article_url": "string",
  "headquarters_location": "city, state",
  "discovery_date": "YYYY-MM-DD",
  "signal_strength": "high|medium"
}
```

**Signal Strength Scoring**:
- **High**: Series B+ in last 60 days, $20M+
- **Medium**: Series B+ in last 90 days, or Series A with $10M+

---

### 3. Office Real Estate News

#### Why This Signal Matters
Direct evidence of office moves, expansions, or new locations = immediate furniture needs.

#### Data Sources

**Dallas Business Journal - Real Estate Section**
- **Access**: Some free articles, subscription for full access
- **Free Approach**: 
  - RSS feeds
  - Google News searches for DBJ articles
  - Web scraping of free articles
- **Topics**: Office leases, relocations, expansions

**Bisnow Dallas-Fort Worth**
- Commercial real estate news platform
- **Access**: Free email newsletter, some free articles
- **Scraping**: Check robots.txt, respect rate limits
- **URL**: `https://www.bisnow.com/dallas-fort-worth`

**CoStar News (Limited Free Access)**
- Commercial real estate data
- Some news articles available without subscription
- Focus on major lease transactions

**Dallas Morning News - Business Section**
- Local news source
- Business real estate announcements
- Free articles available

**Fort Worth Star-Telegram - Business**
- Similar to Dallas Morning News
- Fort Worth-specific announcements

**Google News API Search**
- **Query Examples**:
  - `"office lease" AND (Dallas OR "Fort Worth" OR Plano OR Frisco)`
  - `"headquarters" AND "moving" AND Dallas`
  - `"office expansion" AND DFW`
  - `"new office" AND (Dallas OR Plano OR Frisco)`
- Filter by date: last 90 days
- 100 free requests per day

**Commercial Real Estate Brokers' Press Releases**
- CBRE, JLL, Cushman & Wakefield, Transwestern
- Often announce major lease transactions
- Press release pages are public and scrapable

#### Keywords to Monitor
- "office lease"
- "headquarters relocation"
- "office expansion"
- "new office location"
- "corporate campus"
- "workspace"
- "lease renewal" (with expansion)
- "build-to-suit"
- "office buildout"

#### Output Schema
```json
{
  "source": "real_estate_news",
  "company_name": "string",
  "announcement_type": "lease|relocation|expansion|new_office",
  "square_footage": "integer (if available)",
  "location": "address or area",
  "move_date": "YYYY-MM-DD (estimated)",
  "announcement_date": "YYYY-MM-DD",
  "news_source": "string",
  "article_url": "string",
  "article_headline": "string",
  "discovery_date": "YYYY-MM-DD",
  "signal_strength": "high"
}
```

**Signal Strength**: Almost always **High** - this is explicit buying intent

---

### 4. Certificate of Occupancy (CO) Records

#### Why This Signal Matters
**This is a GOLD MINE signal.** A Certificate of Occupancy means:
- Construction is complete
- Company is about to move in (within 30-60 days typically)
- They need to furnish the space NOW
- This is public record data (ethical and legal)

#### Data Sources

**Dallas County**
- **Dallas Development Services**: https://dallascityhall.com/departments/sustainabledevelopment
- **Building Inspection Records**: May have online portal
- **Open Records Request**: Can request CO data via Texas Public Information Act

**Tarrant County (Fort Worth)**
- **Tarrant County Building Permits**: Online portal available
- **Fort Worth Development Services**

**Collin County (Plano, Frisco, McKinney)**
- **City-level permits**: Each city maintains own records
- **Plano Building Inspections**: Online portal
- **Frisco Building Department**: Online portal

**Denton County**
- City-level permits

#### Access Methods

**Option 1: Online Portals (Preferred)**
Many cities have online permit/CO search portals:
- Search by permit type: "Certificate of Occupancy"
- Filter by property type: "Commercial", "Office"
- Filter by issue date: Last 30 days
- Export results (if available)

**Option 2: API Access (If Available)**
Some jurisdictions offer data APIs or data downloads:
- Check city open data portals
- Dallas Open Data Portal: https://www.dallasopendata.com/
- May have building permits dataset

**Option 3: Public Records Request**
- Submit Texas Public Information Act request
- Request: "All Certificates of Occupancy issued for commercial office properties in the last 90 days"
- Usually free or minimal cost
- May take 10-14 days

**Option 4: Third-Party Data Aggregators**
- **BuildingConnected** (commercial construction data)
- **Construct Connect** (may have free tier or trial)
- **Dodge Data & Analytics** (paid but may offer samples)

#### Data Points to Extract
- **Property Address**
- **Certificate Issue Date**
- **Property Owner/Company Name** (if available)
- **Square Footage**
- **Property Type** (Office, Mixed-Use, etc.)
- **Permit Number** (for reference)
- **Occupancy Classification**

#### Implementation Approach
```
Weekly batch process:
1. Check each county/city portal for new COs (last 7 days)
2. Filter for "Office" or "Commercial" properties
3. Filter by square footage: >5,000 sq ft (meaningful office space)
4. Extract company/owner information
5. Cross-reference with business databases to get actual company name
   (property owner might be LLC, need to find actual operating company)
6. Write to Excel: Raw Discoveries
```

#### Output Schema
```json
{
  "source": "certificate_of_occupancy",
  "property_address": "string",
  "city": "string",
  "county": "string",
  "certificate_issue_date": "YYYY-MM-DD",
  "property_owner": "string",
  "actual_company_name": "string (if identified)",
  "square_footage": "integer",
  "property_type": "office|mixed_use|retail",
  "permit_number": "string",
  "jurisdiction": "City of Dallas|Fort Worth|etc.",
  "discovery_date": "YYYY-MM-DD",
  "signal_strength": "very_high",
  "estimated_move_in_date": "YYYY-MM-DD (CO date + 30-60 days)"
}
```

**Signal Strength**: **Very High** - immediate need, known timeline

#### Challenges & Solutions

**Challenge 1**: Property owner is LLC, not actual company
- **Solution**: Use commercial property databases (LoopNet, CoStar) to cross-reference
- **Solution**: Google search the address to find company press releases
- **Solution**: Check company websites for "locations" pages

**Challenge 2**: Mixed-use properties
- **Solution**: Focus on office component square footage
- **Solution**: Filter by occupancy classification codes for office use

**Challenge 3**: Data access varies by jurisdiction
- **Solution**: Start with Dallas and Plano (usually have better online portals)
- **Solution**: Build relationships with city permit offices for regular data pulls

---

### 5. Commercial Remodel Permits

#### Why This Signal Matters
Companies pulling remodel permits for existing office space often need:
- New furniture to replace old
- Additional furniture for layout changes
- Upgraded furniture for modernization
- Timeline: Usually 60-120 days from permit to completion

#### Data Sources

**Same as Certificate of Occupancy sources:**
- Dallas County Building Inspections
- Tarrant County Building Permits
- Collin County city permit portals
- Denton County city permit portals

#### Permit Types to Monitor
- "Commercial Remodel"
- "Tenant Improvement" (TI)
- "Office Renovation"
- "Interior Alteration - Commercial"
- "Building Alteration - Office"

#### Implementation Approach
```
Weekly batch process:
1. Check permit portals for new commercial remodel permits
2. Filter for office properties
3. Filter by project value: >$100K (meaningful renovation)
4. Extract company information
5. Estimate completion date (permit date + typical timeline)
6. Write to Excel: Raw Discoveries
```

#### Output Schema
```json
{
  "source": "remodel_permit",
  "property_address": "string",
  "city": "string",
  "county": "string",
  "permit_issue_date": "YYYY-MM-DD",
  "permit_type": "string",
  "project_value": "integer (if available)",
  "property_owner": "string",
  "actual_company_name": "string (if identified)",
  "square_footage": "integer (if available)",
  "contractor_name": "string",
  "project_description": "string (if available)",
  "estimated_completion_date": "YYYY-MM-DD",
  "discovery_date": "YYYY-MM-DD",
  "signal_strength": "high"
}
```

**Signal Strength Scoring**:
- **Very High**: Project value >$500K, office-specific renovation
- **High**: Project value $100K-$500K
- **Medium**: Project value <$100K (might be minor updates)

#### Key Data Points
- **Project Value**: Higher value = more likely to need furniture
- **Contractor**: Knowing the contractor can help (some specialize in office buildouts)
- **Timeline**: Permits typically take 3-6 months to complete

---

## Implementation Plan

### Week 1: Infrastructure & Job Postings
**Goal**: Get first discovery source operational

**Tasks**:
1. Set up Python development environment
2. Create Excel template with 5 sheets (Raw Discoveries, Enriched, Scored, Ready for Outreach, Historical)
3. Build Indeed job posting scraper
   - Respect robots.txt and rate limits
   - Target DFW area
   - Target job titles
   - Write to Excel
4. Test with sample searches
5. Document any issues

**Deliverable**: 20-50 companies discovered via job postings

---

### Week 2: Public Records (CO & Permits)
**Goal**: Add the highest-quality signals

**Tasks**:
1. Research Dallas County CO/permit portal access
   - Document login process (if needed)
   - Identify data export options
   - Test manual extraction
2. Research other DFW county portals
3. Build CO scraper/extractor
   - Start with Dallas County (easiest)
   - Filter for commercial office properties
   - Extract company information
   - Handle LLC → company name mapping
4. Build remodel permit scraper/extractor
   - Same approach as CO
5. Combine with job posting data in Excel

**Deliverable**: 10-30 companies from public records

---

### Week 3: News & Funding
**Goal**: Complete all discovery sources

**Tasks**:
1. Set up Google News API
   - Get API key (free tier)
   - Build search queries for all three topics:
     * Funding announcements
     * Real estate news
     * Office moves/expansions
2. Set up Crunchbase scraping or API
   - Start with free tier API
   - Filter for DFW companies
   - Recent funding only
3. Add Dallas Business Journal RSS monitoring
4. Combine all discovery sources into unified pipeline
5. Build deduplication logic
   - Same company discovered via multiple signals = stronger lead
6. Test end-to-end

**Deliverable**: Full discovery pipeline operational, 50-100 companies discovered

---

### Week 4: Refinement & Automation
**Goal**: Polish and prepare for production

**Tasks**:
1. Add error handling and logging
2. Build notification system (email alerts for errors)
3. Create weekly run schedule
4. Document process for future maintenance
5. Review discovered companies with Jason
6. Adjust filters based on feedback

**Deliverable**: Production-ready discovery agent

---

## Technical Architecture

### Technology Stack
- **Language**: Python 3.10+
- **Web Scraping**: 
  - `requests` + `BeautifulSoup4` for simple scraping
  - `Playwright` for JavaScript-heavy sites
  - `scrapy` for larger-scale scraping (optional)
- **Data Storage**: 
  - `openpyxl` for Excel writing
  - `pandas` for data manipulation
- **APIs**: 
  - `requests` for API calls
  - `feedparser` for RSS feeds
- **Scheduling**: 
  - Manual runs initially
  - `schedule` library for automation (or cron)

### Project Structure
```
lead_mining_agent/
├── discovery_agent/
│   ├── __init__.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── job_postings.py
│   │   ├── funding_news.py
│   │   ├── real_estate_news.py
│   │   ├── certificates_of_occupancy.py
│   │   └── remodel_permits.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── excel_writer.py
│   │   ├── deduplication.py
│   │   └── logging_setup.py
│   └── main.py
├── config/
│   ├── config.yaml (API keys, settings)
│   └── keywords.yaml (search terms, job titles)
├── data/
│   └── leads_repository.xlsx
├── logs/
│   └── discovery_agent.log
├── requirements.txt
└── README.md
```

### Configuration File Example
```yaml
# config/config.yaml

geographic_scope:
  cities:
    - Dallas
    - Fort Worth
    - Plano
    - Frisco
    - McKinney
    - Irving
    - Arlington
  counties:
    - Dallas
    - Tarrant
    - Collin
    - Denton

job_posting:
  target_titles:
    - "Facilities Manager"
    - "Director of Facilities"
    - "VP Real Estate"
    - "Office Manager"
    - "Workplace Manager"
  sources:
    - indeed
    - glassdoor
  rate_limit_seconds: 2

funding:
  minimum_amount_millions: 10
  funding_rounds:
    - "Series B"
    - "Series C"
    - "Series D"
    - "Series E"
  lookback_days: 90

real_estate:
  keywords:
    - "office lease"
    - "headquarters relocation"
    - "office expansion"
    - "new office"
  lookback_days: 90

public_records:
  co_min_sqft: 5000
  remodel_min_value: 100000
  lookback_days: 30

api_keys:
  google_news: "YOUR_API_KEY"
  crunchbase: "YOUR_API_KEY"
```

---

## Data Quality & Deduplication

### Deduplication Logic

Companies can be discovered through multiple sources. When this happens:
1. **Merge into single record** with all signals listed
2. **Increase signal strength score** (multiple signals = higher confidence)
3. **Track all discovery sources** for context

**Matching Logic**:
- Primary: Company domain (if available)
- Secondary: Company name (fuzzy matching, handle variations)
- Tertiary: Address (for public records)

### Data Validation

**Company Name Validation**:
- Check if name is valid company (not individual, not generic)
- Verify it's not a property management company or landlord
- Validate it's a real operating business

**Location Validation**:
- Ensure location is within DFW target area
- Standardize city names (Dallas vs. Dallas, TX)

**Date Validation**:
- Ensure dates are within lookback window
- Flag stale data (>90 days old)

---

## Output: Excel Raw Discoveries Sheet

### Column Structure

| Column | Description | Example |
|--------|-------------|---------|
| Discovery Date | When we found this company | 2024-11-24 |
| Company Name | Name of company | Acme Corp |
| Domain | Company website | acme.com |
| Discovery Source | How we found them | certificate_of_occupancy |
| Signal Type | Category of signal | public_record |
| Signal Strength | Very High / High / Medium / Low | Very High |
| Signal Date | When the trigger event occurred | 2024-11-20 |
| Details | Specifics about the signal | CO issued for 15,000 sqft office at 123 Main St |
| Location | City, State | Dallas, TX |
| Timeline | Estimated need timeline | Immediate (within 60 days) |
| Source URL | Reference link | https://dallascityhall.com/... |
| County | County where signal originated | Dallas County |
| All Signals | If multiple discoveries, list all | CO + Job Posting |
| Notes | Any additional context | New headquarters |

---

## Success Metrics

### Discovery Volume (Weekly Targets)
- **Job Postings**: 10-20 companies
- **Funding News**: 2-5 companies (DFW has active startup scene)
- **Real Estate News**: 5-10 companies
- **Certificates of Occupancy**: 10-15 companies
- **Remodel Permits**: 5-10 companies

**Total Weekly Discovery Target**: 30-60 companies

### Quality Metrics
- **% within ICP**: Target 70%+ (50-999 employees, target industries)
- **% with multiple signals**: Target 20%+ (indicates strong buying intent)
- **% with verifiable contact info**: Target 80%+

### Timeline to Value
- **Week 1**: First companies discovered
- **Week 3**: Full pipeline operational
- **Week 4**: First leads sent to SDR team

---

## Cost Analysis

### Free Sources
- Indeed job scraping: **$0**
- Google News API: **$0** (free tier)
- Public records (CO/permits): **$0** (or minimal filing fees)
- RSS feeds: **$0**
- Company website scraping: **$0**

### Low-Cost Options (Optional)
- Crunchbase Pro: **$29/month** (for better API access)
- Dallas Business Journal digital subscription: **$50-100/year** (for full article access)
- Proxy services (if needed for scraping): **$10-30/month**

### Total Phase 1 Cost
**$0-50/month** vs. ZoomInfo at **$15,000+/year**

**ROI**: If even one deal closes from this system, it pays for itself 100x over.

---

## Risks & Mitigation

### Risk 1: Public Records Not Available Online
**Mitigation**: 
- Start with cities that have online portals (Dallas, Plano)
- Use Public Information Act requests as backup
- Build relationships with city permit offices

### Risk 2: Rate Limiting / IP Blocking
**Mitigation**:
- Respect rate limits (1-2 requests per second)
- Add delays between requests
- Use residential proxies if needed
- Rotate user agents

### Risk 3: Company Name Extraction from Public Records
**Mitigation**:
- Use address-based lookup in commercial property databases
- Google search addresses to find company press releases
- Cross-reference with company "locations" pages
- Manual verification for high-value leads

### Risk 4: Data Freshness
**Mitigation**:
- Run weekly (not daily) to keep data fresh without overwhelming
- Focus on recent signals only (30-90 days)
- Timestamp all data for staleness tracking

---

## Next Steps

1. **Review this plan** with Jason - any adjustments needed?

2. **Prioritize discovery sources** - confirm all 5 are in scope for Phase 1

3. **Research DFW public records access**:
   - Dallas County CO/permit portal
   - Collin County access
   - Tarrant County access

4. **Set up development environment**:
   - Python virtual environment
   - Install dependencies
   - Create Excel template

5. **Begin Week 1 development**: Job posting scraper

---

## Future Enhancements (Phase 2+)

### Geographic Expansion
- Austin (Travis County, Williamson County)
- Houston (Harris County)
- San Antonio (Bexar County)

### Additional Signal Sources
- Google Analytics (Vari website visitors)
- LinkedIn company growth tracking (headcount increases)
- SEC filings (for public companies)
- Industry-specific news sources

### Automation
- Daily automated runs
- Automated email alerts for high-priority leads
- Salesforce integration (auto-create leads)

### ML/AI Enhancements
- Predictive lead scoring based on historical conversions
- NLP analysis of news articles for sentiment
- Company similarity scoring (lookalike modeling)

---

## Questions for Jason

1. Do you have any existing relationships with city permit offices that could help with data access?

2. For Certificate of Occupancy leads - what's the typical sales cycle timeline from CO issuance to furniture order?

3. Are there specific DFW submarkets that are higher priority? (e.g., Plano/Frisco vs. Downtown Dallas)

4. Should we exclude certain property types? (e.g., medical office buildings, coworking spaces)

5. What's the minimum office size (square footage) that's worth pursuing?

6. Any known competitors' furniture in the DFW market we should be aware of?

---

## Appendix: DFW Public Records Resources

### Dallas County
- **Website**: https://dallascityhall.com/departments/sustainabledevelopment
- **Building Inspections**: https://developmentservices.dallascityhall.com/
- **Permit Search**: Available online (requires registration)
- **Open Data**: https://www.dallasopendata.com/

### Tarrant County (Fort Worth)
- **Website**: https://www.fortworthtexas.gov/departments/development-services
- **Permit Portal**: Online search available
- **Contact**: 817-392-7653

### Collin County Cities

**Plano**
- **Website**: https://www.plano.gov/329/Building-Inspections
- **Permit Search**: Online portal available
- **Contact**: 972-941-7160

**Frisco**
- **Website**: https://www.friscotexas.gov/197/Building-Inspections
- **Online Portal**: Available
- **Contact**: 972-292-5600

**McKinney**
- **Website**: https://www.mckinneytexas.org/691/Building-Inspection
- **Permit Search**: Online available
- **Contact**: 972-547-7555

### Denton County
- Most permits handled at city level (Denton, Lewisville, etc.)
- Check individual city websites

### Commercial Real Estate Data
- **LoopNet**: Free basic search (property listings)
- **CoStar**: Paid (expensive) but may have trial
- **CBRE Research**: Some free market reports
- **JLL Research**: Some free market reports

---

**Document Version**: 1.0  
**Date**: November 24, 2024  
**Author**: Jason Belote with Claude
