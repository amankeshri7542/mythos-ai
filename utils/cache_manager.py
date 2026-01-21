# utils/cache_manager.py
import os
import hashlib
import json
import shutil
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Separate folders for different types
        self.image_cache = self.cache_dir / "images"
        self.audio_cache = self.cache_dir / "audio"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        self.image_cache.mkdir(exist_ok=True)
        self.audio_cache.mkdir(exist_ok=True)
        
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _generate_hash(self, *args):
        """Generate unique hash from arguments"""
        combined = "|".join(str(arg) for arg in args)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached_image(self, prompt, ref_path, scene_index):
        """Retrieve cached image if exists"""
        cache_key = self._generate_hash(prompt, ref_path, scene_index)
        
        if cache_key in self.metadata:
            cached_path = self.image_cache / self.metadata[cache_key]["filename"]
            
            if cached_path.exists():
                return str(cached_path)
        
        return None
    
    def cache_image(self, image_path, prompt, ref_path, scene_index):
        """Save image to cache"""
        cache_key = self._generate_hash(prompt, ref_path, scene_index)
        filename = f"{cache_key}.png"
        cached_path = self.image_cache / filename
        
        # Copy image to cache
        shutil.copy(image_path, cached_path)
        
        # Update metadata
        self.metadata[cache_key] = {
            "filename": filename,
            "prompt": prompt,
            "ref_path": ref_path,
            "scene_index": scene_index,
            "type": "image"
        }
        
        self._save_metadata()
        return str(cached_path)
    
    def get_cached_audio(self, text, voice):
        """Retrieve cached audio if exists"""
        cache_key = self._generate_hash(text, voice)
        
        if cache_key in self.metadata:
            cached_path = self.audio_cache / self.metadata[cache_key]["filename"]
            
            if cached_path.exists():
                return str(cached_path)
        
        return None
    
    def cache_audio(self, audio_path, text, voice):
        """Save audio to cache"""
        cache_key = self._generate_hash(text, voice)
        filename = f"{cache_key}.mp3"
        cached_path = self.audio_cache / filename
        
        # Copy audio to cache
        shutil.copy(audio_path, cached_path)
        
        # Update metadata
        self.metadata[cache_key] = {
            "filename": filename,
            "text": text,
            "voice": voice,
            "type": "audio"
        }
        
        self._save_metadata()
        return str(cached_path)
    
    def clear_cache(self):
        """Clear all cached files"""
        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.image_cache.mkdir(exist_ok=True)
        self.audio_cache.mkdir(exist_ok=True)
        self.metadata = {}
        self._save_metadata()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        total_images = len(list(self.image_cache.glob("*.png")))
        total_audio = len(list(self.audio_cache.glob("*.mp3")))
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        return {
            "total_images": total_images,
            "total_audio": total_audio,
            "cache_size_mb": round(size_mb, 2)
        }