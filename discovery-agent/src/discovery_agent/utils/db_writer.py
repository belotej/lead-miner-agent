"""
Database writer utility for saving leads to the Django SQLite database.
This module allows the discovery agent to save leads directly to the database
without needing to import the full Django framework.
"""

import sqlite3
import os
import logging
from datetime import datetime


class DatabaseWriter:
    """Writes leads to the SQLite database used by the Django admin."""

    def __init__(self, db_path=None):
        self.logger = logging.getLogger(__name__)

        if db_path is None:
            # Default path: lead_miner_web/db.sqlite3
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to discovery-agent, then to parent, then to lead_miner_web
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            db_path = os.path.join(project_root, 'lead_miner_web', 'db.sqlite3')

        self.db_path = db_path
        self.logger.info(f"Database path: {self.db_path}")

        if not os.path.exists(self.db_path):
            self.logger.error(f"Database not found at {self.db_path}. Run Django migrations first.")
            raise FileNotFoundError(f"Database not found at {self.db_path}")

    def save_leads(self, leads):
        """
        Save a list of lead dictionaries to the database.
        Skips duplicates based on source_url.
        Returns tuple of (saved_count, skipped_count).
        """
        if not leads:
            self.logger.info("No leads to save.")
            return (0, 0)

        saved_count = 0
        skipped_count = 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for lead in leads:
            try:
                # Parse discovery_date
                discovery_date = lead.get('discovery_date', datetime.now().strftime('%Y-%m-%d'))

                # Extract industry from details if present (for job postings)
                industry = lead.get('industry', '')
                if not industry and 'Industry:' in lead.get('details', ''):
                    # Try to extract from details string
                    details = lead.get('details', '')
                    if 'Industry:' in details:
                        start = details.find('Industry:') + 9
                        end = details.find('.', start)
                        if end > start:
                            industry = details[start:end].strip()

                cursor.execute('''
                    INSERT INTO leads_lead (
                        company_name, domain, discovery_source, signal_type,
                        signal_strength, discovery_date, signal_date, details,
                        location, timeline, source_url, county, all_signals,
                        notes, status, industry, created_at, updated_at,
                        contact_name, contact_email, contact_phone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead.get('company_name', 'Unknown'),
                    lead.get('domain', ''),
                    lead.get('discovery_source', ''),
                    lead.get('signal_type', ''),
                    lead.get('signal_strength', 'Medium'),
                    discovery_date,
                    lead.get('signal_date', ''),
                    lead.get('details', ''),
                    lead.get('location', ''),
                    lead.get('timeline', 'Unknown'),
                    lead.get('source_url', ''),
                    lead.get('county', ''),
                    lead.get('all_signals', ''),
                    lead.get('notes', ''),
                    'new',  # Default status
                    industry,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    lead.get('contact_name', ''),
                    lead.get('contact_email', ''),
                    lead.get('contact_phone', ''),
                ))
                saved_count += 1

            except sqlite3.IntegrityError as e:
                # Duplicate source_url - skip
                skipped_count += 1
                self.logger.debug(f"Skipped duplicate: {lead.get('company_name')} - {lead.get('source_url')}")
            except Exception as e:
                self.logger.error(f"Error saving lead {lead.get('company_name')}: {e}")
                skipped_count += 1

        conn.commit()
        conn.close()

        self.logger.info(f"Saved {saved_count} leads to database. Skipped {skipped_count} duplicates.")
        return (saved_count, skipped_count)

    def get_lead_count(self):
        """Return total number of leads in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM leads_lead')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_recent_source_urls(self, days=7):
        """Get source URLs from the last N days to check for duplicates before API calls."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT source_url FROM leads_lead
            WHERE discovery_date >= date('now', ?)
        ''', (f'-{days} days',))
        urls = set(row[0] for row in cursor.fetchall())
        conn.close()
        return urls
