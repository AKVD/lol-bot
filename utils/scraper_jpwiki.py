import requests
from bs4 import BeautifulSoup
import re

# Global cache
_cached_db_soup = None

def get_japanese_skills(champion_name):
    """
    Extracts Japanese skill data from loljp-wiki database page.
    Returns dict with skill data in Japanese.
    """
    global _cached_db_soup
    
    # Fetch and cache the database page
    if _cached_db_soup is None:
        url = "https://www.loljp-wiki.jp/wiki/?%A5%C7%A1%BC%A5%BF%A5%D9%A1%BC%A5%B9%2F%A5%C1%A5%E3%A5%F3%A5%D4%A5%AA%A5%F3"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'euc-jp'
            _cached_db_soup = BeautifulSoup(r.content, 'lxml')
        except Exception as e:
            print(f"Error fetching Japanese Wiki: {e}")
            return None
    
    soup = _cached_db_soup
    text = soup.get_text()
    
    # Map common English names to Japanese for better matching
    from utils.champion_map import get_japanese_name
    jp_name = get_japanese_name(champion_name)
    
    # Try to find champion - look for pattern: "ChampionName(EnglishName)"
    # IMPORTANT: Must be at the start of a line to avoid matching skill names
    patterns = [
        rf'(?:^|\n){re.escape(jp_name)}\s*\([^)]+\)',  # Japanese(English) at line start
        rf'(?:^|\n)[^(]+\({re.escape(champion_name)}\)',  # SomeName(English) at line start
    ]
    
    match = None
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            break
    
    if not match:
        return None
    
    # Found champion - extract section
    start_pos = match.start()
    
    # Look for next champion entry to know where to stop
    # Champions are formatted as: Name(English) followed by (Ranged) or (Melee) marker
    # Increased range significantly to ensure we capture all 5 skills including edge cases
    end_match = re.search(r'\n\n[^\n]+\([A-Z][a-z]+\)\s*\n\((?:Ranged|Melee)\)', text[start_pos+150:start_pos+8000])
    
    if end_match:
        section = text[start_pos:start_pos+150+end_match.start()]
    else:
        section = text[start_pos:start_pos+5500]  # Further increased to be absolutely sure
    
    # Parse skills - IMPROVED ALGORITHM
    skills = {}
    lines = section.split('\n')
    
    skill_keys = ['P', 'Q', 'W', 'E', 'R']
    i = 0
    
    while i < len(lines) and len(skills) < 5:
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
        
        # Strict skill name detection: line with parentheses
        if '(' in line and ')' in line:
            # Skip obvious non-skill lines - SIMPLIFIED to avoid false negatives
            if any(line.startswith(prefix) for prefix in [
                'Active:', 'Passive:', '1st', '2nd', '3rd', '4th', 
                'Toggle:', 'Cost:', 'CD:', 'Range:', 'DM:', 
               'Crit', '%('
            ]):
                continue
            
            # Skip if line starts with "HP:" or stats patterns
            if re.match(r'^(HP|最大|増加|追加|物理|魔法|レベル):', line):
                continue                
            # Look ahead: is there an Active/Passive/Toggle line soon?
            found_skill_marker = False
            lookahead_limit = 8  # Increased from 5 to handle more edge cases
            for j in range(i, min(i + lookahead_limit, len(lines))):
                ahead_line = lines[j].strip()
                # Match Active/Toggle/Channeled
                if re.match(r'^(?:Active|Toggle|Togggle|Channeled)[\s:-]', ahead_line, re.IGNORECASE):
                    found_skill_marker = True
                    break
                # Match "Passive:" OR "1st Passive:", "2nd Passive:" etc (these are sub-effects of main passive)
                if re.match(r'^(?:\d+(?:st|nd|rd|th)\s+)?Passive[\s:]', ahead_line, re.IGNORECASE):
                    found_skill_marker = True
                    break
                # If we hit another skill name first, stop
                if '(' in ahead_line and ')' in ahead_line and j > i:
                    break
            
            if found_skill_marker:
                # This is a skill!
                skill_name = line
                skill_desc_lines = []
                
                # Collect all description lines until next skill name
                while i < len(lines):
                    desc_line = lines[i].strip()
                    
                    # Check if this is the start of another skill
                    if ('(' in desc_line and ')' in desc_line and 
                        not desc_line.startswith(('Active:', 'Passive:', '1st', '2nd', 'Cost:', 'CD:', 'Range:', 'HP:', 'DM:'))):
                        # Peek ahead to confirm it's a skill
                        is_next_skill = False
                        for k in range(i+1, min(i+4, len(lines))):
                            if re.match(r'^(?:(?:Passive|Active|Toggle))[\s:-]', lines[k].strip(), re.IGNORECASE):
                                # Make sure it's not "1st Passive", "2nd Passive"
                                if not re.match(r'^\d+(st|nd|rd|th)\s+Passive', lines[k].strip(), re.IGNORECASE):
                                    is_next_skill = True
                                    break
                        if is_next_skill:
                            # Next skill found, stop here
                            break
                    
                    # Add this line to description
                    if desc_line and len(skill_desc_lines) < 20:
                        skill_desc_lines.append(desc_line)
                    
                    i += 1
                    
                    # Stop if we've collected enough or hit next champion
                    if len(skill_desc_lines) > 15 and ('Cost:' in desc_line or 'CD:' in desc_line):
                        break
                
                # Save the skill
                if skill_desc_lines and len(skills) < 5:
                    skill_key = skill_keys[len(skills)]
                    skills[skill_key] = {
                        'name': skill_name,
                        'description': '\n'.join(skill_desc_lines),
                        'stats': {}
                    }
    
    # Special case: Quinn's R skill (manual addition due to parsing difficulties)
    if champion_name.lower() == 'quinn' and len(skills) == 4 and 'R' not in skills:
        skills['R'] = {
            'name': '相棒(Behind Enemy Lines)',
            'description': '''Togggle On: 2秒の詠唱後、ヴァロールが空から降りてきて飛ばせてくれる。効果中はMSが増加するが、敵チャンピオンか敵タワーから攻撃を受けると3秒間増加MSが消滅する。このスキルは使用後にスカイストライク(Skystrike)に変化し、再使用可能になる。また、AAや鷲の眼(W)以外のスキル使用か、効果消滅時に自動的に再使用する。
増加MS: 70/100/130%
Cost: 100/50/0MN　CD: 3s

スカイストライク: ヴァロールが空中に戻り、周囲の敵ユニットに物理DMと、付近の敵ユニット1体に弱点(4.5s)を付与する。
物理DM: 60/90/120 + (35%増加AD)
Cost: 無し　Range: 700''',
            'stats': {}
        }
    
    return skills if len(skills) >= 2 else None
