# utils/error_handler.py
import time
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries=3,
    initial_delay=2,
    exponential_base=2,
    exceptions=(Exception,)
):
    """
    Decorator that retries a function with exponential backoff
    
    Example:
    - Attempt 1 fails: wait 2 seconds
    - Attempt 2 fails: wait 4 seconds
    - Attempt 3 fails: wait 8 seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting {func.__name__} (try {attempt + 1}/{max_retries})")
                    result = func(*args, **kwargs)
                    
                    if result is not None:
                        logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                        return result
                    
                    # If result is None, treat as failure
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ {func.__name__} returned None, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= exponential_base
                    
                except exceptions as e:
                    logger.error(f"❌ {func.__name__} failed: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= exponential_base
                    else:
                        logger.error(f"Max retries reached for {func.__name__}")
                        return None
            
            return None
        
        return wrapper
    return decorator


class ProgressTracker:
    """Track progress and allow resuming from failures"""
    
    def __init__(self):
        self.completed_scenes = {}
        self.failed_scenes = []
    
    def mark_complete(self, scene_index, image_path, audio_path):
        """Mark a scene as successfully generated"""
        self.completed_scenes[scene_index] = {
            "image": image_path,
            "audio": audio_path,
            "status": "complete"
        }
    
    def mark_failed(self, scene_index, error):
        """Mark a scene as failed"""
        self.failed_scenes.append({
            "scene_index": scene_index,
            "error": str(error)
        })
    
    def is_complete(self, scene_index):
        """Check if scene is already generated"""
        return scene_index in self.completed_scenes
    
    def get_progress(self):
        """Get current progress statistics"""
        return {
            "completed": len(self.completed_scenes),
            "failed": len(self.failed_scenes),
            "total": len(self.completed_scenes) + len(self.failed_scenes)
        }