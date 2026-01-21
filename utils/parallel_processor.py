# utils/parallel_processor.py
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

class ParallelSceneProcessor:
    def __init__(self, max_workers=3):
        """
        max_workers=3 means we can generate 3 things at once
        Don't set too high or you'll hit API rate limits
        """
        self.max_workers = max_workers
    
    def process_scenes_parallel(self, scenes, image_generator, audio_generator):
        """
        Process multiple scenes in parallel
        
        Args:
            scenes: List of scene dictionaries
            image_generator: Function to generate images
            audio_generator: Function to generate audio
        
        Returns:
            List of results: [(scene_index, image_path, audio_path), ...]
        """
        results = []
        
        if not isinstance(scenes, list):
            logger.error(f"❌ process_scenes_parallel expected list of dicts, got {type(scenes)}")
            return []
            
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            
            for i, scene in enumerate(scenes):
                if not isinstance(scene, dict):
                    logger.warning(f"⚠️ Skipping invalid scene at index {i}: {type(scene)}")
                    continue
                    
                # Submit image generation
                img_future = executor.submit(image_generator, scene, i)
                # Submit audio generation
                audio_future = executor.submit(audio_generator, scene, i)
                
                futures[i] = {
                    "image": img_future,
                    "audio": audio_future,
                    "scene": scene
                }
            
            # Collect results as they complete
            for scene_index in sorted(futures.keys()):
                try:
                    img_path = futures[scene_index]["image"].result(timeout=120)
                    audio_path = futures[scene_index]["audio"].result(timeout=60)
                    
                    results.append((scene_index, img_path, audio_path))
                    logger.info(f"✅ Scene {scene_index} completed")
                    
                except Exception as e:
                    logger.error(f"❌ Scene {scene_index} failed: {str(e)}")
                    results.append((scene_index, None, None))
        
        return results