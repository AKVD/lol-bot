# Champion Map with Auto-Update Support
# This file can be auto-generated from the Wiki

import os
import json
from datetime import datetime, timedelta

# Cache file to store auto-generated champion list
CACHE_FILE = 'utils/champion_cache.json'
CACHE_DURATION_DAYS = 7  # Update every week

def load_champion_cache():
    """Load champion list from cache file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(days=CACHE_DURATION_DAYS):
                    return data.get('champions', {})
        except:
            pass
    return None

def save_champion_cache(champions):
    """Save champion list to cache file."""
    data = {
        'timestamp': datetime.now().isoformat(),
        'champions': champions
    }
    os.makedirs('utils', exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_champions_from_wiki():
    """Fetch champions from Wiki (only if cache is expired)."""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        
        url = "https://www.loljp-wiki.jp/wiki/?%A5%C7%A1%BC%A5%BF%A5%D9%A1%BC%A5%B9%2F%A5%C1%A5%E3%A5%F3%A5%D4%A5%AA%A5%F3"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'euc-jp'
        soup = BeautifulSoup(r.content, 'lxml')
        text = soup.get_text()
        
        pattern = r'(?:^|\n)([^(\n]+)\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\)\s*\n\((?:Ranged|Melee)\)'
        matches = re.findall(pattern, text, re.MULTILINE)
        
        champion_map = {}
        for jp_name, en_name in matches:
            jp_name = jp_name.strip()
            en_name = en_name.strip().replace(' ', '')
            
            if jp_name and en_name:
                en_lower = en_name.lower()
                champion_map[en_lower] = en_name
                champion_map[jp_name] = en_name
        
        if champion_map:
            save_champion_cache(champion_map)
        
        return champion_map
    except Exception as e:
        print(f"Failed to fetch champions from Wiki: {e}")
        return None

# Try to load from cache first, fetch if needed
_cached_champions = load_champion_cache()
if _cached_champions is None:
    print("Updating champion list from Wiki...")
    _cached_champions = fetch_champions_from_wiki()
    if _cached_champions:
        print(f"Loaded {len(_cached_champions)//2} champions from Wiki")

# Fallback to manual list if auto-fetch fails
from utils.champion_map_manual import CHAMPION_MAP_MANUAL

# Combine auto-fetched and manual champions
CHAMPION_MAP = {}
if _cached_champions:
    CHAMPION_MAP.update(_cached_champions)
# Add manual overrides/nicknames
CHAMPION_MAP.update(CHAMPION_MAP_MANUAL)

# ... (rest of the functions remain the same)
