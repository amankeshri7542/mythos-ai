# =========================================================
# Mythos AI Studio - Production Version
# Complete with: Rate Limiting, Caching, Error Recovery, Parallel Processing
# =========================================================

import os
import shutil
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Import configuration
from config import Config

# Import utilities
from utils.rate_limiter import RateLimiter
from utils.cache_manager import CacheManager
from utils.error_handler import retry_with_exponential_backoff, ProgressTracker
from utils.parallel_processor import ParallelSceneProcessor
from utils.validators import validate_topic

# Import services
from services.script_generator import generate_script
from services.image_generator import generate_image_img2img, generate_image_txt2img
from services.tts_service import generate_audio
from services.video_assembler import add_subtitles_to_image, create_video_clip, assemble_final_video

# Import models
from models.character_db import get_character_reference_from_topic

# ============ ENVIRONMENT SETUP ============
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not OPENAI_API_KEY or not STABILITY_API_KEY:
    st.error("❌ Missing API keys in .env file!")
    st.stop()

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ============ INITIALIZE MANAGERS ============
rate_limiter = RateLimiter(max_videos_per_day=Config.MAX_VIDEOS_PER_DAY)
cache_manager = CacheManager(cache_dir=Config.CACHE_DIR)

# ============ UI STYLING ============
st.set_page_config(page_title="Mythos AI Studio", page_icon="🕉️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Eczar:wght@400;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #1a0b00 0%, #000000 50%, #1a0b00 100%);
    }
    
    h1 {
        font-family: 'Cinzel', serif;
        background: linear-gradient(45deg, #fbbf24, #f59e0b, #d97706);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(251, 191, 36, 0.5);
        font-size: 3.5rem;
        text-align: center;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px #fbbf24); }
        to { filter: drop-shadow(0 0 20px #f59e0b); }
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #d97706, #92400e);
        color: white;
        font-family: 'Cinzel', serif;
        font-size: 1.3rem;
        padding: 15px 40px;
        border-radius: 10px;
        border: 2px solid #f59e0b;
        box-shadow: 0 5px 15px rgba(245, 158, 11, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.6);
    }
    
    .stTextInput>div>input {
        background: rgba(41, 21, 5, 0.8);
        color: #ffedd5;
        border: 2px solid #d97706;
        border-radius: 8px;
        font-size: 1.1rem;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ============ HELPER FUNCTIONS ============

def get_client_ip():
    """Get user identifier for rate limiting"""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return "unknown-session"
        return "user-session"
    except Exception:
        return "unknown-session"

# ============ WRAPPED FUNCTIONS WITH RETRY ============

@retry_with_exponential_backoff(max_retries=3, initial_delay=2)
def generate_image_safe(scene_prompt, ref_image_path, scene_index):
    """Image generation with retry and caching"""
    # Normalize ref_image_path for caching key
    cache_ref = ref_image_path if ref_image_path else "none"
    
    # Check cache first
    cached = cache_manager.get_cached_image(scene_prompt, cache_ref, scene_index)
    if cached and os.path.exists(cached):
        st.caption("✅ Using cached image")
        output = f"scene_{scene_index}.png"
        shutil.copy(cached, output)
        return output
    
    # Generate new image
    if ref_image_path:
        result = generate_image_img2img(scene_prompt, ref_image_path, scene_index, STABILITY_API_KEY)
    else:
        result = generate_image_txt2img(scene_prompt, scene_index, STABILITY_API_KEY)
    
    # Cache result
    if result:
        cache_manager.cache_image(result, scene_prompt, cache_ref, scene_index)
    
    return result

@retry_with_exponential_backoff(max_retries=3, initial_delay=1)
def generate_audio_safe(text, index):
    """TTS with retry and caching"""
    from services.tts_service import choose_voice
    
    voice = choose_voice(text)
    
    # Check cache
    cached = cache_manager.get_cached_audio(text, voice)
    if cached and os.path.exists(cached):
        output = f"audio_{index}.mp3"
        shutil.copy(cached, output)
        return output
    
    # Generate new audio
    result = generate_audio(text, index)
    
    # Cache result
    if result:
        cache_manager.cache_audio(result, text, voice)
    
    return result

# ============ VIDEO CREATION (PARALLEL) ============

def create_video_parallel(script, topic):
    """Create video with parallel scene generation"""
    
    processor = ParallelSceneProcessor(max_workers=Config.MAX_WORKERS)
    
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    status_container.markdown("🚀 **Generating scenes in parallel...**")
    
    # Wrapper functions for parallel processing
    def image_wrapper(scene, index):
        visual_desc = scene.get("image_prompt", "")
        ref_path = get_character_reference_from_topic(visual_desc) or \
                   get_character_reference_from_topic(scene.get("narration", "")) or \
                   get_character_reference_from_topic(topic)
        
        return generate_image_safe(visual_desc, ref_path, index)
    
    def audio_wrapper(scene, index):
        narration = scene.get("narration", "")
        return generate_audio_safe(narration, index)
    
    # Process all scenes in parallel
    results = processor.process_scenes_parallel(script, image_wrapper, audio_wrapper)
    
    # Build clips
    clips = []
    success_count = 0
    
    for scene_index, img_file, audio_file in results:
        if img_file and audio_file:
            narration = script[scene_index].get("narration", "")
            img_with_sub = add_subtitles_to_image(img_file, narration)
            
            try:
                clip = create_video_clip(img_with_sub, audio_file)
                clips.append(clip)
                success_count += 1
            except Exception as e:
                st.warning(f"⚠️ Scene {scene_index + 1} clip failed: {str(e)}")
        
        progress_bar.progress((scene_index + 1) / len(script))
    
    if success_count == 0:
        st.error("❌ No scenes generated successfully")
        return None
    
    st.info(f"✅ {success_count}/{len(script)} scenes generated")
    
    # Assemble video
    status_container.markdown("✨ **Assembling final masterpiece...**")
    return assemble_final_video(clips)

# ============ ANALYTICS DASHBOARD ============

def show_analytics():
    """Display analytics in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Analytics")
    
    # Rate limiter stats
    stats = rate_limiter.get_stats()
    st.sidebar.metric("Users Today", stats["unique_users_today"])
    st.sidebar.metric("Videos Today", stats["total_videos_today"])
    
    # Cache stats
    cache_stats = cache_manager.get_cache_stats()
    st.sidebar.metric("Cached Images", cache_stats["total_images"])
    st.sidebar.metric("Cached Audio", cache_stats["total_audio"])
    st.sidebar.metric("Cache Size (MB)", cache_stats["cache_size_mb"])
    
    if st.sidebar.button("🗑️ Clear Cache"):
        cache_manager.clear_cache()
        st.sidebar.success("Cache cleared!")

# ============ MAIN UI ============

st.title("🕉️ Mythos AI Studio")
st.markdown("""
<div style='text-align: center; color: #fbbf24; font-size: 1.2rem; margin-bottom: 2rem;'>
    ✨ Transform Ancient Tales into Cinematic Masterpieces ✨
</div>
""", unsafe_allow_html=True)

# Feature highlights
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🎬 AI Director")
    st.caption("GPT-4 powered scripts")
with col2:
    st.markdown("### 🎨 Visual Mastery")
    st.caption("Stable Diffusion XL")
with col3:
    st.markdown("### 🎙️ Divine Voice")
    st.caption("Neural TTS narration")

st.markdown("---")

# Input
topic = st.text_input(
    "🌟 Enter Your Mythological Vision",
    placeholder="Examples: Krishna playing flute in Vrindavan, Hanuman lifting the mountain",
    help="Describe your scene in Hindi or English"
)

# Examples
with st.expander("💡 Need Inspiration?"):
    st.markdown("""
    **Single Character:**
    - `Krishna playing flute under moonlight`
    - `Hanuman meditating in Himalayas`
    - `Shiva dancing the cosmic dance`
    
    **Hindi:**
    - `हनुमान जी संजीवनी पर्वत उठाते हुए`
    - `कृष्ण और राधा यमुना के किनारे`
    """)

# Quota display
user_key = rate_limiter.get_user_key(get_client_ip())
can_proceed, current_count, remaining = rate_limiter.check_limit(user_key)

col1, col2 = st.columns([3, 1])
with col1:
    st.progress(current_count / Config.MAX_VIDEOS_PER_DAY)
with col2:
    st.metric("Quota", f"{remaining}/{Config.MAX_VIDEOS_PER_DAY}")

st.markdown("---")

# Generate button
if st.button("🚀 Create Epic Video", use_container_width=True):
    # Validate input
    valid, error_msg = validate_topic(topic)
    if not valid:
        st.error(error_msg)
        st.stop()
    
    # Check rate limit
    if not can_proceed:
        st.error(f"🚫 **Daily Limit Reached!**")
        st.info(f"Come back tomorrow! 🌅 ({current_count}/3 used)")
        st.stop()
    
    # Generate script
    with st.spinner("📜 Writing ancient scripture..."):
        try:
            script = generate_script(topic, openai_client)
            if not script:
                st.error("Script generation failed")
                st.stop()
        except Exception as e:
            st.error(f"❌ Script error: {str(e)}")
            st.stop()
    
    # Show script
    with st.expander("📖 View Script"):
        st.json(script)
    
    if not isinstance(script, list):
        st.error(f"❌ internal error: Generated script is not a list of scenes. Got: {type(script)}")
        st.stop()

    # Create video
    video_path = create_video_parallel(script, topic)
    
    if video_path and os.path.exists(video_path):
        # Increment usage
        rate_limiter.increment_usage(user_key)
        
        st.success(f"✅ Video created! ({current_count + 1}/{Config.MAX_VIDEOS_PER_DAY} used today)")
        st.video(video_path)
        
        with open(video_path, "rb") as f:
            st.download_button(
                "⬇️ Download Video",
                f,
                file_name="mythos_saga.mp4",
                mime="video/mp4"
            )
    else:
        st.error("❌ Video creation failed")

# Show analytics
show_analytics()