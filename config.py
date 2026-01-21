# =========================================================
# Mythos AI Studio - Configuration
# =========================================================

class Config:
    # Rate Limiting
    MAX_VIDEOS_PER_DAY = 3
    
    # Script Generation
    MAX_SCRIPT_SCENES = 4
    GPT_MODEL = "gpt-4o"
    
    # Image Generation
    IMAGE_SIZE = (1024, 1024)
    STABILITY_MODEL = "stable-diffusion-xl-1024-v1-0"
    
    # Image Quality Settings
    DEFAULT_CFG_SCALE = "8"
    DEFAULT_STEPS = "40"
    DEFAULT_SAMPLER = "K_DPMPP_2M"
    
    # Subtitle Settings
    SUBTITLE_FONT_SIZE = 40
    SUBTITLE_MAX_WIDTH = 50
    
    # Parallel Processing
    MAX_WORKERS = 2  # Number of concurrent scene generations
    
    # Paths
    CACHE_DIR = "cache"
    DATA_DIR = "data"
    CHARACTERS_DIR = "characters"
    
    # Camera Presets
    CAMERA_PRESETS = [
        "wide cinematic shot, full body, epic scale",
        "medium shot, three-quarter profile, dynamic action pose",
        "low-angle heroic shot, looking up at character, majestic presence",
        "close-up divine portrait, intense expression, detailed facial features"
    ]
    
    # Character Mapping
    CHARACTER_MAP = {
        # Shiva variations
        "shiva": "characters/Shiva.png",
        "mahadev": "characters/Shiva.png",
        "shankar": "characters/Shiva.png",
        "bholenath": "characters/Shiva.png",
        
        # Hanuman variations
        "hanuman": "characters/Hanuman.png",
        "bajrang": "characters/Hanuman.png",
        "bajrangbali": "characters/Hanuman.png",
        "pavanputra": "characters/Hanuman.png",
        
        # Krishna variations
        "krishna": "characters/Krishna.png",
        "kanha": "characters/Krishna.png",
        "govinda": "characters/Krishna.png",
        "madhav": "characters/Krishna.png",
        "vasudev": "characters/Krishna.png",
        
        # Rama variations
        "rama": "characters/Rama.png",
        "ram": "characters/Rama.png",
        "raghav": "characters/Rama.png",
        "raghunath": "characters/Rama.png",
    }