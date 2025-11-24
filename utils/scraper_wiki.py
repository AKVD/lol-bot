import requests
from bs4 import BeautifulSoup
import re

# Try to import Japanese Wiki scraper
try:
    from utils.scraper_jpwiki import get_japanese_skills as get_jp_skills
    HAS_JP_WIKI = True
except:
    HAS_JP_WIKI = False

def get_champion_skills(champion_name):
    """
    Scrapes for champion skills (P, Q, W, E, R).
    Tries Japanese Wiki first, falls back to English Wiki.
    Returns a dictionary: {'P': {...}, 'Q': {...}, ...}
    """
    # Try Japanese Wiki first for native Japanese descriptions
    if HAS_JP_WIKI:
        jp_skills = get_jp_skills(champion_name)
        if jp_skills and len(jp_skills) >= 3:  # At least got some skills
            return jp_skills
    
    # Fallback to English Wiki
    return get_english_wiki_skills(champion_name)

def get_english_wiki_skills(champion_name):
    """
    Scrapes LoL Wiki for champion skills (P, Q, W, E, R).
    Returns a dictionary: {'P': {...}, 'Q': {...}, ...}
    """
    name_for_url = champion_name.replace(' ', '_')
    if name_for_url.lower() == 'wukong': name_for_url = 'Wukong'
    
    url = f"https://leagueoflegends.fandom.com/wiki/{name_for_url}/LoL"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch Wiki: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        skills = {}
        
        # Find all skill containers
        skill_containers = soup.find_all('div', {'class': 'skill'})
        
        if not skill_containers:
            return None

        keys_ordered = ['P', 'Q', 'W', 'E', 'R']
        
        for i, container in enumerate(skill_containers):
            if i >= len(keys_ordered): break
            
            key = keys_ordered[i]
            
            # Extract skill name from h3 > span.mw-headline
            name_tag = container.find('h3')
            if name_tag:
                name_span = name_tag.find('span', {'class': 'mw-headline'})
                name = name_span.get_text(strip=True) if name_span else "Unknown"
            else:
                name = "Unknown"
            
            # Extract description
            # The description is usually in the text after "Innate:" or "Active:" or "Passive:"
            # Let's get all text and try to find the description
            text_content = container.get_text(separator=' ', strip=True)
            
            # Try to find the description part (after "Innate:" "Active:" etc.)
            desc_match = re.search(r'(?:Innate|Active|Passive|Toggle):\s*(.+?)(?:$|(?:Cooldown|Cost|Range))', text_content, re.DOTALL)
            if desc_match:
                description = desc_match.group(1).strip()
                # Clean up excessive whitespace
                description = re.sub(r'\s+', ' ', description)
            else:
                # Fallback: try to get text from ability-info-container
                info_container = container.find('div', {'class': 'ability-info-container'})
                if info_container:
                    # Get all paragraphs or text
                    description = info_container.get_text(separator=' ', strip=True)[:500]
                    description = re.sub(r'\s+', ' ', description)
                else:
                    description = "No description available."
            
            # Extract stats (Cooldown, Cost, Range) from the portable-infobox
            stats = {}
            
            infobox = container.find('aside', {'class': 'portable-infobox'})
            if infobox:
                # Find all data items
                data_items = infobox.find_all('div', {'class': 'pi-item', 'data-source': True})
                
                for item in data_items:
                    data_source = item.get('data-source', '')
                    value_div = item.find('div', {'class': 'pi-data-value'})
                    
                    if value_div:
                        value = value_div.get_text(strip=True)
                        
                        if 'cooldown' in data_source.lower():
                            stats['cooldown'] = value
                        elif 'cost' in data_source.lower():
                            stats['cost'] = value
                        elif 'range' in data_source.lower():
                            stats['range'] = value

            skills[key] = {
                'name': name,
                'description': description,
                'stats': stats
            }
            
        return skills if skills else None

    except Exception as e:
        print(f"Error scraping Wiki: {e}")
        return None
