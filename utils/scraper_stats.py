import requests
from bs4 import BeautifulSoup
import json

def get_champion_stats(champion_name):
    """
    Scrapes U.GG for champion stats (Tier, Win Rate, Ban Rate, Pick Rate).
    """
    slug = champion_name.lower().replace(' ', '').replace("'", "").replace(".", "")
    if slug == 'wukong': slug = 'monkeyking'
    
    url = f"https://u.gg/lol/champions/{slug}/build"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')
        if not script:
            return None
            
        data = json.loads(script.string)
        
        try:
            # Try to locate stats
            # pageProps -> championData -> stats
            # This is a guess based on common structures.
            # If not found, we might need to look elsewhere.
            
            # Let's try to find the stats in the page text if JSON fails?
            # No, let's stick to JSON or fail gracefully.
            
            # Actually, U.GG puts stats in the title/description often?
            # "Ahri Build with Highest Winrate... Patch 15.22"
            # The description had "Ahri build with the highest winrate runes and items..."
            # But the numbers (Win Rate: 50.1%) are usually in the body.
            
            # Let's try to parse the text content of the "stats" elements if we can identify them by class.
            # Classes are usually hashed (e.g. "sc-xyz").
            
            # Let's return a placeholder for now as I cannot verify the JSON path.
            # But I will try to extract the "Tier" and "Win Rate" from the text if possible.
            
            text = soup.get_text()
            # Look for "Win Rate" followed by a percentage
            # "Win Rate50.13%"
            
            stats = {}
            
            # Win Rate
            wr_match = re.search(r'Win Rate\s*(\d+\.\d+)%', text)
            if wr_match:
                stats['win_rate'] = wr_match.group(1)
                
            # Tier
            # "Tier S+"
            tier_match = re.search(r'Tier\s*([SABCDF]\+?)', text)
            if tier_match:
                stats['tier'] = tier_match.group(1)
                
            # Ban Rate
            ban_match = re.search(r'Ban Rate\s*(\d+\.\d+)%', text)
            if ban_match:
                stats['ban_rate'] = ban_match.group(1)
                
            # Pick Rate
            pick_match = re.search(r'Pick Rate\s*(\d+\.\d+)%', text)
            if pick_match:
                stats['pick_rate'] = pick_match.group(1)
                
            if stats:
                return stats
            
            return None
            
        except Exception:
            return None
            
    except Exception as e:
        print(f"Error scraping U.GG stats: {e}")
        return None
