import requests
from bs4 import BeautifulSoup
import re

def get_counters(champion_name, role=None, rank='emerald_plus'):
    """
    Scrapes U.GG for counter matchups.
    
    Args:
        champion_name: Champion slug
        role: Optional lane ('top', 'middle', 'jungle', 'bottom', 'support')
        rank: Rank tier (default: 'emerald_plus')
    
    Returns a list of dictionaries with champion name and win rate (Ahri's win rate against them).
    Sorted by win rate ascending (best counters for the enemy first).
    """
    slug = champion_name.lower().replace(' ', '').replace("'", "").replace(".", "")
    if slug == 'wukong': slug = 'monkeyking'
    
    # Base URL
    url = f"https://u.gg/lol/champions/{slug}/counter"
    
    # Add query parameters
    params = []
    if rank:
        params.append(f"rank={rank}")
    if role:
        params.append(f"role={role}")
    
    if params:
        url += "?" + "&".join(params)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch U.GG: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        matchups = []
        
        # Find all links that look like champion pages
        # The structure in the markdown chunk was [NameWinRate% WRGames](url)
        # In HTML, this is likely an <a> tag containing several divs or spans.
        # We look for the row that contains the champion name and win rate.
        
        # U.GG structure is complex. Let's try to find the specific container.
        # Often there is a "rt-tr-group" or similar for tables.
        # Or we can iterate over all links and try to parse the text.
        
        links = soup.find_all('a', href=re.compile(r'/lol/champions/.*/build'))
        
        seen_champs = set()

        for link in links:
            text = link.get_text(separator=' ') # Use separator to avoid merging words
            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Pattern: Name WinRate% WR Games Matches/games
            # Example: Malzahar 49.19% WR 2,275 Matches OR 2,275 games
            # Updated regex to be more flexible and capture the number after WR
            
            match = re.search(r'([a-zA-Z\s\']+?)\s*(\d+\.\d+)%\s*WR\s*([\d,]+)', text)
            
            if match:
                name = match.group(1).strip()
                win_rate = float(match.group(2))
                matches_str = match.group(3).replace(',', '')
                
                try:
                    matches = int(matches_str)
                except ValueError:
                    matches = 0
                
                # Filter by minimum matches (default 100 to ensure reliability)
                if matches < 100:
                    continue
                
                # Avoid duplicates and self
                if name.lower() == champion_name.lower():
                    continue
                if name in seen_champs:
                    continue
                
                seen_champs.add(name)
                matchups.append({'name': name, 'win_rate': win_rate, 'matches': matches})
        
        # Sort by win rate ascending (Lower win rate for me = Harder matchup = Better counter)
        matchups.sort(key=lambda x: x['win_rate'])
        
        return matchups

    except Exception as e:
        print(f"Error scraping U.GG: {e}")
        return []
