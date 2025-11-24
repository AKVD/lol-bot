import re

def format_skill_numbers(text):
    """
    Formats skill description to highlight important numbers.
    Makes damage values, cooldowns, costs, etc. stand out using Discord markdown.
    """
    if not text:
        return text
    
    # Highlight damage numbers (e.g., "40/60/80/100/120")
    # Pattern: numbers separated by slashes
    text = re.sub(r'(\d+(?:/\d+)+)', r'**\1**', text)
    
    # Highlight standalone important numbers followed by context
    # e.g., "35 + (3.529 × (Lv - 1))"
    text = re.sub(r'(\d+(?:\.\d+)?)\s*\+\s*\(([^)]+)\)', r'**\1** + (\2)', text)
    
    # Highlight cooldown values (e.g., "CD: 7s" or "クールダウン: 7s")
    text = re.sub(r'(CD|クールダウン):\s*(\d+(?:/\d+)*(?:\.\d+)?s?)', r'\1: **\2**', text)
    
    # Highlight cost values (e.g., "Cost: 30MN" or "コスト: 30MN")
    text = re.sub(r'(Cost|コスト):\s*(\d+(?:/\d+)*\s*(?:MN|マナ|HP|体力)?)', r'\1: **\2**', text)
    
    # Highlight range values
    text = re.sub(r'(Range|射程):\s*(\d+)', r'\1: **\2**', text)
    
    # Highlight percentages (e.g., "40%")
    text = re.sub(r'(\d+(?:\.\d+)?)%', r'**\1%**', text)
    
    return text
