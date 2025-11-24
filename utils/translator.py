# English to Japanese translation dictionary for skill descriptions

SKILL_TRANSLATIONS = {
    # Action verbs
    'deals': 'を与える',
    'damage': 'ダメージ',
    'magic damage': '魔法ダメージ',
    'physical damage': '物理ダメージ',
    'true damage': '確定ダメージ',
    'bonus': 'ボーナス',
    'increases': '増加',
    'decreased': '減少',
    'gains': '獲得',
    'grants': '付与',
    'sends': '送る',
    'fires': '発射',
    'dashes': 'ダッシュ',
    'blinks': '瞬間移動',
    'throws': '投げる',
    'charges': 'チャージ',
    'channels': '詠唱',
    'casts': '発動',
    'activates': '発動',
    'passive': 'パッシブ',
    'active': 'アクティブ',
    'innate': '固有',
    
    # Stats
    'attack damage': '攻撃力',
    'ability power': 'AP',
    'armor': '物理防御',
    'magic resistance': '魔法防御',
    'health': '体力',
    'mana': 'マナ',
    'movement speed': '移動速度',
    'attack speed': '攻撃速度',
    'cooldown': 'クールダウン',
    'cost': 'コスト',
    'range': '射程',
    
    # Common terms
    'champion': 'チャンピオン',
    'enemy': '敵',
    'enemies': '敵',
    'target': 'ターゲット',
    'ally': '味方',
    'minion': 'ミニオン',
    'monster': 'モンスター',
    'seconds': '秒',
    'seconds.': '秒',
    'maximum': '最大',
    'minimum': '最小',
    'additional': '追加の',
    'bonus': 'ボーナス',
    'base': '基本',
    'total': '合計',
    'per': 'ごとに',
    'for': 'の間',
    'over': '秒間',
    'against': 'に対して',
    'nearby': '近くの',
    'visible': '視認できる',
    'area': '範囲',
    'direction': '方向',
    'location': '地点',
    
    # Skill-specific common phrases
    'in the target direction': 'ターゲット方向に',
    'at the target location': 'ターゲット地点に',
    'to the target': 'ターゲットに',
    'within': '以内の',
    'around': '周囲の',
    'hit by': 'に当たった',
    'struck by': 'に当たった',
}

def translate_skill_text(text):
    """
    Translates English skill text to Japanese using keyword replacement.
    This is a basic translation that replaces common terms.
    """
    if not text:
        return text
    
    translated = text
    
    # Replace each term (case-insensitive where appropriate)
    for eng, jap in SKILL_TRANSLATIONS.items():
        # Use word boundaries for better matching
        import re
        pattern = r'\b' + re.escape(eng) + r'\b'
        translated = re.sub(pattern, jap, translated, flags=re.IGNORECASE)
    
    return translated
