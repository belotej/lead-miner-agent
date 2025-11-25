import re
from difflib import SequenceMatcher

class Deduplication:
    def __init__(self):
        pass

    def deduplicate_raw_items(self, items, similarity_threshold=0.85):
        """
        Deduplicate raw RSS items based on Title similarity.
        Keeps the first occurrence.
        """
        unique_items = []
        seen_titles = []

        for item in items:
            title = item.get('title', '')
            # Normalize title (remove special chars, lowercase)
            clean_title = re.sub(r'[^\w\s]', '', title).lower().strip()
            
            if not clean_title:
                continue

            is_duplicate = False
            for seen_title in seen_titles:
                # Check similarity
                ratio = SequenceMatcher(None, clean_title, seen_title).ratio()
                if ratio > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
                seen_titles.append(clean_title)
                
        return unique_items

    def deduplicate(self, leads):
        return leads
