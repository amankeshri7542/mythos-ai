# =========================================================
# Text-to-Speech Service
# =========================================================

import asyncio
import edge_tts

def detect_language_for_tts(text):
    """Detect language for voice selection"""
    if not text:
        return "en"
    
    for ch in text:
        if '\u0900' <= ch <= '\u097F':
            return "hi"
    
    return "en"

def choose_voice(text):
    """Select appropriate voice based on language"""
    lang = detect_language_for_tts(text)
    
    if lang == "hi":
        return "hi-IN-MadhurNeural"  # Hindi male voice
    else:
        return "en-IN-PrabhatNeural"  # English Indian male voice

def generate_audio(text, index):
    """Generate audio using edge-tts"""
    voice = choose_voice(text)
    filename = f"audio_{index}.mp3"
    
    async def run_tts():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filename)
    
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run TTS
        loop.run_until_complete(run_tts())
        return filename
    
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")