# =========================================================
# Character Database - God-Specific Attributes
# =========================================================

import os
from config import Config

def get_character_attributes(god_name):
    """Get god-specific visual attributes for enhanced prompting"""
    gn = god_name.lower()
    
    if "hanuman" in gn or "bajrang" in gn:
        return """
        powerful muscular physique, divine golden-orange fur with ethereal glow,
        calm wise expression with compassionate eyes,
        ornate gold jewelry and sacred thread (yagnopavit),
        divine gada (mace) with intricate carvings nearby,
        subtle divine aura radiating peaceful strength,
        traditional dhoti, humble yet powerful presence
        """
    
    elif "krishna" in gn or "kanha" in gn:
        return """
        serene divine blue skin with soft luminescence,
        peacock feather crown (mor pankh) with jeweled ornaments,
        gentle loving smile, playing bamboo flute (bansuri),
        flowing yellow silk dhoti with gold embroidery (pitambara),
        divine radiance emanating compassion and joy,
        lotus eyes, graceful posture
        """
    
    elif "shiva" in gn or "mahadev" in gn:
        return """
        meditative calm expression, ash-smeared blue-grey skin (vibhuti),
        crescent moon and holy cobra (nag) in matted hair (jata),
        third eye closed in peaceful meditation,
        rudraksha beads mala and tiger skin,
        trident (trishul) nearby, simple austere appearance,
        cosmic energy swirling subtly around divine form
        """
    
    elif "ram" in gn or "raghu" in gn:
        return """
        noble warrior-king posture, regal yet humble bearing,
        traditional crown (mukut) and royal silk garments,
        bow (dhanush) and quiver of divine arrows,
        righteous peaceful expression, embodiment of dharma,
        soft golden aura of divinity and justice,
        calm dignified presence, green or saffron dhoti
        """
    
    else:
        return """
        divine mythological character, traditional Indian attire,
        peaceful powerful presence, subtle divine aura,
        ornate jewelry and sacred symbols
        """

def get_character_reference_from_topic(text):
    """Find character reference image based on text"""
    if not text:
        return None
    
    t = text.lower()
    
    # If mentions multiple characters, use txt2img instead
    multi_char_indicators = [" and ", " with ", " along with ", ","]
    if any(indicator in t for indicator in multi_char_indicators):
        return None
    
    # Find matching character
    for key, filepath in Config.CHARACTER_MAP.items():
        if key in t:
            if os.path.exists(filepath):
                return filepath
    
    return None