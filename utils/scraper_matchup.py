import requests
from bs4 import BeautifulSoup
import re

def get_matchup_info(champion1, champion2, role=None):
    """
    Fetches matchup information between two champions from U.GG.
    
    Args:
        champion1: Main champion slug
        champion2: Opponent champion slug
        role: Optional lane
    
    Returns:
        Dictionary with matchup data or None
    """
    slug1 = champion1.lower().replace(' ', '').replace("'", "").replace(".", "")
    slug2 = champion2.lower().replace(' ', '').replace("'", "").replace(".", "")
    
    if slug1 == 'wukong': slug1 = 'monkeyking'
    if slug2 == 'wukong': slug2 = 'monkeyking'
    
    # U.GG matchup URL
    url = f"https://u.gg/lol/champions/{slug1}/matchups"
    
    # Add query parameters
    params = []
    params.append("rank=emerald_plus")
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
            print(f"Failed to fetch matchup data: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the specific matchup in the page
        # Look for links that contain the second champion's name
        links = soup.find_all('a', href=re.compile(r'/lol/champions/.*/build'))
        
        for link in links:
            text = link.get_text(separator=' ', strip=True)
            
            # Check if this is the matchup we're looking for
            # The text should contain the champion2's name
            if champion2.lower() in text.lower() or slug2 in text.lower():
                # Try to extract win rate
                # Pattern: Name WinRate% WR
                match = re.search(r'([\d.]+)%\s*WR', text)
                if match:
                    win_rate = float(match.group(1))
                    
                    # Determine difficulty based on win rate
                    if win_rate >= 52:
                        difficulty = "有利"
                        difficulty_en = "Favorable"
                    elif win_rate >= 48:
                        difficulty = "互角"
                        difficulty_en = "Even"
                    else:
                        difficulty = "不利"
                        difficulty_en = "Unfavorable"
                    
                    # Try to extract matches count
                    matches_match = re.search(r'([\d,]+)\s*Matches', text)
                    matches = matches_match.group(1) if matches_match else "?"
                    
                    return {
                        'champion1': champion1,
                        'champion2': champion2,
                        'win_rate': win_rate,
                        'difficulty': difficulty,
                        'difficulty_en': difficulty_en,
                        'matches': matches,
                        'url': url
                    }
        
        # If we didn't find the specific matchup, return None
        return None

    except Exception as e:
        print(f"Error scraping matchup data: {e}")
        return None
