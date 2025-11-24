import json
import os

def get_bot_synergies(champion_name):
    """
    Get synergy recommendations for bot lane.
    Returns list of synergistic champions with reasons.
    
    Args:
        champion_name: Champion slug (normalized)
    
    Returns:
        List of dicts with 'name' and 'reason' keys, or None if not found
    """
    # Load synergy database
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot_synergies.json')
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            synergies_db = json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading synergies: {e}")
        return None
    
    # Normalize champion name
    champ_key = champion_name.lower().replace(' ', '').replace("'", "").replace(".", "")
    
    # Special cases
    if champ_key == 'wukong':
        champ_key = 'monkeyking'
    
    # Get synergies
    if champ_key in synergies_db:
        return synergies_db[champ_key].get('top_synergies', [])
    
    return None
