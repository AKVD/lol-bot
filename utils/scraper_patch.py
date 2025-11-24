import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def _translate_skill_key(skill_key):
    """Translate English skill keys to Japanese"""
    translations = {
        'Passive': 'パッシブ',
        'PASSIVE': 'パッシブ',
        'Base Stats': 'ステータス',
        'BASE STATS': 'ステータス',
        'Innate': 'パッシブ',
        'INNATE': 'パッシブ',
        'General': '一般',
        'GENERAL': '一般'
    }
    
    # Check direct match first
    if skill_key in translations:
        return translations[skill_key]
    
    # For "Passive - Skill Name" format, extract and translate
    if ' - ' in skill_key:
        parts = skill_key.split(' - ', 1)
        key = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else ''
        
        if key in translations:
            # Return Japanese key + English name for now
            return f"{translations[key]} - {name}"
        elif key.upper() in ['Q', 'W', 'E', 'R']:
            # Keep Q/W/E/R as is, they're universal
            return skill_key
    
    # Return as-is if no translation found
    return skill_key

def get_patch_history(champion_name, count=3):
    """
    Fetches detailed patch history for a champion from official Riot Games patch notes.
    Returns only the latest patch by default.
    """
    try:
        from utils.champion_map import get_japanese_name
        jp_name = get_japanese_name(champion_name)
        
        # Get latest patch number
        latest_patch = get_latest_patch_number()
        
        if not latest_patch:
            return {
                'champion': jp_name,
                'patches': [],
                'message': '最新パッチ情報の取得に失敗しました',
                'wiki_url': 'https://www.leagueoflegends.com/ja-jp/news/tags/patch-notes/'
            }
        
        # Try to find changes in recent patches (traverse backwards if needed)
        max_lookback = 10  # Check up to 10 recent patches
        patches_to_check = [latest_patch]
        
        # Generate list of recent patch numbers to check
        # Parse patch number (e.g., "25.23" -> major=25, minor=23)
        try:
            major, minor = map(int, latest_patch.split('.'))
            for i in range(1, max_lookback):
                minor -= 1
                if minor < 1:
                    # Go to previous major version
                    major -= 1
                    minor = 24  # Assuming max 24 patches per year
                    if major < 13:  # Don't go too far back
                        break
                patches_to_check.append(f"{major}.{minor}")
        except:
            # If parsing fails, just check the latest
            pass
        
        # Try each patch until we find changes
        changes = None
        url_used = None
        patch_version_found = None
        
        for patch_num in patches_to_check:
            # Fetch patch notes for this patch
            # URL format uses hyphens instead of dots: patch-25-23-notes
            patch_url_ja = f"https://www.leagueoflegends.com/ja-jp/news/game-updates/patch-{patch_num.replace('.', '-')}-notes/"
            patch_url_en = f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{patch_num.replace('.', '-')}-notes/"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            # Try Japanese first, fallback to English
            try:
                r = requests.get(patch_url_ja, headers=headers, timeout=15)
                if r.status_code == 200:
                    changes = _extract_champion_changes(r.text, champion_name, 'ja')
                    if changes:
                        url_used = patch_url_ja
                        patch_version_found = patch_num
            except:
                pass
            
            if changes is None:
                try:
                    r = requests.get(patch_url_en, headers=headers, timeout=15)
                    if r.status_code == 200:
                        changes = _extract_champion_changes(r.text, champion_name, 'en')
                        if changes:
                            url_used = patch_url_en
                            patch_version_found = patch_num
                except:
                    pass
            
            # If we found changes, stop searching
            if changes:
                break
        
        
        if changes is None or not changes:
            return {
                'champion': jp_name,
                'patches': [],
                'message': f'{jp_name}の最近{max_lookback}パッチに変更が見つかりませんでした',
                'wiki_url': url_used if url_used else f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{latest_patch.replace('.', '-')}-notes/"
            }
        
        # Display note if not from latest patch
        note = ''
        if patch_version_found and patch_version_found != latest_patch:
            note = f'（最新パッチ {latest_patch} に変更なし。最後の変更: {patch_version_found}）'
        
        patch_info = {
            'version': f'V{patch_version_found if patch_version_found else latest_patch}',
            'version_num': tuple(map(int, (patch_version_found if patch_version_found else latest_patch).split('.'))),
            'changes': changes,
            'note': note
        }
        
        return {
            'champion': jp_name,
            'patches': [patch_info],
            'wiki_url': url_used if url_used else f"https://www.leagueoflegends.com/en-us/news/game-updates/patch-{latest_patch.replace('.', '-')}-notes/"
        }
        
    except Exception as e:
        print(f"Error fetching patch history for {champion_name}: {e}")
        import traceback
        traceback.print_exc()
        
        from utils.champion_map import get_japanese_name
        jp_name = get_japanese_name(champion_name)
        
        return {
            'champion': jp_name,
            'patches': [],
            'message': 'パッチ情報の取得に失敗しました',
            'wiki_url': 'https://www.leagueoflegends.com/ja-jp/news/tags/patch-notes/'
        }

def get_latest_patch_number():
    """Get the latest patch number from official patch notes listing"""
    try:
        url = "https://www.leagueoflegends.com/ja-jp/news/tags/patch-notes/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        
        # Look for patch version pattern like "25.23"
        # Pattern: パッチノート 25.23 or patch-25-23-notes
        pattern = r'patch[- ](\d+)[.-](\d+)'
        matches = re.findall(pattern, r.text, re.IGNORECASE)
        
        if matches:
            # Get the first (latest) match
            major, minor = matches[0]
            return f"{major}.{minor}"
        
        return None
        
    except Exception as e:
        print(f"Error fetching latest patch number: {e}")
        return None

def _extract_champion_changes(html_content, champion_name, language='ja'):
    """Extract champion-specific changes from patch notes HTML"""
    changes = []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find the champion section
    # Look for the champion name on its own line (short line with just the name)
    champion_section_start = -1
    
    for i, line in enumerate(lines):
        # Exact match or very close match for champion name
        if champion_name.lower() in line.lower():
            if line.lower() == champion_name.lower() or (champion_name.lower() in line.lower() and len(line) < 30):
                champion_section_start = i
                break
    
    if champion_section_start == -1:
        return None
    
    # Extract lines until we hit another champion section or end
    section_lines = []
    for i in range(champion_section_start + 1, min(champion_section_start + 100, len(lines))):
        line = lines[i]
        
        # Stop if we find another champion (short line that looks like a header)
        if i > champion_section_start + 3:  # Give at least 3 lines after champion name
            # Check if this might be the next champion
            is_potential_champion = (
                len(line) < 30 and 
                not any(keyword in line.lower() for keyword in ['damage', 'cooldown', 'armor', 'attack', ':', 'passive', 'base stats']) and
                len(line) > 0 and line[0].isupper()
            )
            if is_potential_champion:
                break
        
        section_lines.append(line)
    
    if not section_lines:
        return None
    
    # Parse the section
    current_skill = 'General'
    
    for i, line in enumerate(section_lines):
        # Check if this is a skill/ability header
        # Format: "W - Fox-Fire" or "Passive - Something"
        skill_match = re.match(r'^([QWER]|Passive|Base Stats?|Innate)\s*[-–—]\s*(.+)', line, re.IGNORECASE)
        if skill_match:
            skill_key = skill_match.group(1).upper() if skill_match.group(1).upper() in ['Q', 'W', 'E', 'R'] else skill_match.group(1)
            skill_name = skill_match.group(2).strip()
            current_skill = f"{skill_key} - {skill_name}"
            continue
        
        # Check for lines containing arrows (changes)
        # The format is often multi-line:
        #   "Attribute name"
        #   ": value1 ⇒"
        #   "value2"
        
        if '⇒' in line:
            # Found an arrow! This is a change line
            # Collect the full change by looking at surrounding lines
            
            # Look back for attribute name and before value
            attribute = ''
            before_value = ''
            after_value = ''
            
            # Case 1: Line starts with ": value ⇒" (attribute is on previous line)
            if line.startswith(':'):
                # Get before value
                before_value = line.split(':', 1)[1].split('⇒')[0].strip()
                # Get attribute from previous line
                if i >= 1:
                    attribute = section_lines[i-1].strip()
                # Get after value from next line
                if i + 1 < len(section_lines):
                    after_value = section_lines[i + 1].strip()
            
            # Case 2: Line has "attribute: before ⇒ after" all in one
            elif ':' in line:
                parts = line.split(':', 1)
                attribute = parts[0].strip()
                value_part = parts[1].strip()
                before_value = value_part.split('⇒')[0].strip()
                after_value = value_part.split('⇒')[1].strip() if '⇒' in value_part else ''
                # If after value is empty, check next line
                if not after_value and i + 1 < len(section_lines):
                    after_value = section_lines[i + 1].strip()
            
            # Case 3: Line has just "before ⇒ after" (attribute is earlier)
            else:
                parts = line.split('⇒', 1)
                before_value = parts[0].strip()
                after_value = parts[1].strip() if len(parts) > 1 else ''
                
                # Look back for attribute
                if i >= 1:
                    prev = section_lines[i-1]
                    if ':' in prev:
                        attribute = prev.split(':')[0].strip()
                    elif i >= 2:
                        attribute = section_lines[i-2].strip()
                
                # If after value is empty, check next line
                if not after_value and i + 1 < len(section_lines):
                    after_value = section_lines[i + 1].strip()
            
            # Build the description
            if attribute and (before_value or after_value):
                desc = f"{attribute}: {before_value} ⇒ {after_value}"
                change_type = _detect_change_type(desc)
                
                # Translate skill key to Japanese
                translated_skill = _translate_skill_key(current_skill)
                
                changes.append({
                    'skill': translated_skill,
                    'type': change_type,
                    'description': _format_change_description(desc)
                })
    
    return changes if changes else None

def _detect_change_type(text):
    """Detect if change is buff, nerf, or neutral by comparing numbers"""
    # Look for patterns like "X ⇒ Y" or "X → Y"
    pattern = r'([\d.]+)\s*(?:⇒|→)\s*([\d.]+)'
    matches = re.findall(pattern, text)
    
    if matches:
        buffs = 0
        nerfs = 0
        
        for before, after in matches:
            try:
                before_val = float(before)
                after_val = float(after)
                
                if after_val > before_val:
                    buffs += 1
                elif after_val < before_val:
                    nerfs += 1
            except:
                pass
        
        if buffs > nerfs:
            return 'buff'
        elif nerfs > buffs:
            return 'nerf'
    
    # Fallback to keyword detection
    text_lower = text.lower()
    buff_keywords = ['increased', 'improved', 'buffed', 'bonus', 'higher', 'longer', 'restored', 'added']
    nerf_keywords = ['decreased', 'reduced', 'nerfed', 'lower', 'shorter', 'removed', 'penalty']
    
    buff_count = sum(1 for kw in buff_keywords if kw in text_lower)
    nerf_count = sum(1 for kw in nerf_keywords if kw in text_lower)
    
    if buff_count > nerf_count:
        return 'buff'
    elif nerf_count > buff_count:
        return 'nerf'
    
    return 'change'

def _format_change_description(text):
    """Format change description for display"""
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate if too long
    if len(text) > 150:
        text = text[:150] + '...'
    
    return text if text else None
