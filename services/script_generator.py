# =========================================================
# Script Generation Service
# =========================================================

import json
from openai import OpenAI
from config import Config

def detect_language(text):
    """Detect if text is Hindi or English"""
    if not text:
        return "en"
    
    # Check for Devanagari characters
    for ch in text:
        if '\u0900' <= ch <= '\u097F':
            return "hi"
    
    return "en"

def build_script_prompt(topic, language):
    """Build GPT-4 prompt for script generation"""
    lang_instruction = "Narrate ONLY in Hindi (Devanagari script)." if language == "hi" else "Narrate ONLY in English."
    
    return f"""
You are a legendary mythological filmmaker and storyteller specializing in Indian mythology.

Create a VISUALLY STUNNING {Config.MAX_SCRIPT_SCENES}-scene script for this topic:
**Topic**: {topic}

**Critical Requirements**:
1. Each scene must be DISTINCT with different actions/locations
2. {lang_instruction}
3. Keep narration SHORT (maximum 2 sentences per scene)
4. Make descriptions CINEMATIC and VIVID

**Output Format**: Valid JSON array of objects.

Each object must have:
- "narration": The voice-over text ({lang_instruction} Max 2 sentences)
- "image_prompt": Detailed visual description of the scene (environment, action, lighting, mood)

Example structure:
[
  {{
    "narration": "Short dramatic narration here",
    "image_prompt": "Detailed visual scene description with action, environment, lighting"
  }}
]

Focus on: Visual storytelling, dramatic moments, cultural authenticity, spiritual essence.
"""

def generate_script(topic, openai_client):
    """Generate cinematic script using GPT-4"""
    language = detect_language(topic)
    prompt = build_script_prompt(topic, language)
    
    try:
        response = openai_client.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert director of mythological cinema. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        # Clean JSON
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        
        scenes = []
        
        # Handle different response formats
        if isinstance(data, dict):
            if "scenes" in data and isinstance(data["scenes"], list):
                scenes = data["scenes"]
            elif "script" in data and isinstance(data["script"], list):
                scenes = data["script"]
            else:
                # Try to find any list in values
                for value in data.values():
                    if isinstance(value, list):
                        scenes = value
                        break
        elif isinstance(data, list):
            scenes = data
            
        # Validate scenes structure
        valid_scenes = []
        for scene in scenes:
            if isinstance(scene, dict) and "narration" in scene:
                # Ensure image_prompt exists
                if "image_prompt" not in scene:
                    scene["image_prompt"] = scene["narration"]
                valid_scenes.append(scene)
                
        if not valid_scenes:
            # Fallback if no valid structure found
            raise ValueError(f"Could not extract valid scenes from response: {str(data)[:200]}")
            
        return valid_scenes
    
    except Exception as e:
        raise Exception(f"Script generation failed: {str(e)}")