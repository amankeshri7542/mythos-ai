# =========================================================
# Image Generation Service
# =========================================================

import os
import io
import base64
import requests
import PIL.Image
import PIL.ImageEnhance
from config import Config
from models.character_db import get_character_attributes

def build_enhanced_prompt(god_name, scene_description, camera_angle):
    """Build optimized prompt for Stability AI"""
    
    attributes = get_character_attributes(god_name)
    
    # Quality enhancement tokens
    quality_tokens = """
    masterpiece, best quality, ultra detailed, 8k uhd, photorealistic,
    professionally lit, volumetric lighting, ray tracing,
    epic cinematic composition, award-winning photography,
    intricate details, sharp focus, depth of field
    """
    
    # Style consistency
    style_tokens = """
    in style of Raja Ravi Varma classical Indian art,
    divine mythological painting, sacred traditional art,
    culturally authentic, spiritual essence
    """
    
    # Strong negative prompt
    negative_prompt = """
    cartoon, anime, sketch, illustration, cgi, 3d render,
    low quality, blurry, distorted, disfigured, bad anatomy,
    multiple heads, deformed body, ugly face, bad proportions,
    modern clothing, sunglasses, phones, cars, buildings, technology,
    text, watermark, signature, logo, brand names,
    western symbols, crosses, churches,
    violence, blood, gore, weapons in aggressive use,
    extra limbs, missing limbs, cloned face, malformed
    """
    
    positive_prompt = f"""
    {god_name}, maintaining exact same facial features as reference,
    {scene_description},
    {camera_angle},
    {attributes},
    ancient sacred Indian mythological setting,
    divine temple or natural spiritual environment,
    {quality_tokens},
    {style_tokens}
    """
    
    return {
        "positive": positive_prompt.strip(),
        "negative": negative_prompt.strip()
    }

def generate_image_img2img(scene_prompt, ref_image_path, scene_index, stability_api_key):
    """Generate image using img2img with reference"""
    
    # Progressive strength for consistency
    strength_map = [0.30, 0.35, 0.40, 0.45]
    image_strength = strength_map[min(scene_index, len(strength_map) - 1)]
    
    # Rotate camera angles
    camera_angle = Config.CAMERA_PRESETS[scene_index % len(Config.CAMERA_PRESETS)]
    
    # Get god name from reference
    god_name = os.path.basename(ref_image_path).split('.')[0]
    
    # Build prompts
    prompts = build_enhanced_prompt(god_name, scene_prompt, camera_angle)
    
    # Load and prepare reference image
    try:
        with PIL.Image.open(ref_image_path) as img:
            img = img.convert("RGB")
            img = img.resize(Config.IMAGE_SIZE, PIL.Image.LANCZOS)
            
            # Enhance contrast
            enhancer = PIL.ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            init_image_bytes = buf.getvalue()
    except Exception as e:
        raise Exception(f"Image preparation failed: {str(e)}")
    
    # Prepare API request
    files = {"init_image": init_image_bytes}
    data = {
        "init_image_mode": "IMAGE_STRENGTH",
        "image_strength": str(image_strength),
        "text_prompts[0][text]": prompts["positive"],
        "text_prompts[0][weight]": "1.0",
        "text_prompts[1][text]": prompts["negative"],
        "text_prompts[1][weight]": "-1.0",
        "cfg_scale": Config.DEFAULT_CFG_SCALE,
        "samples": "1",
        "steps": Config.DEFAULT_STEPS,
        "sampler": Config.DEFAULT_SAMPLER,
    }
    
    headers = {
        "Authorization": f"Bearer {stability_api_key}",
        "Accept": "application/json"
    }
    
    # Make API call
    response = requests.post(
        f"https://api.stability.ai/v1/generation/{Config.STABILITY_MODEL}/image-to-image",
        headers=headers,
        files=files,
        data=data,
        timeout=90
    )
    
    if response.status_code != 200:
        raise Exception(f"Stability AI error: {response.text}")
    
    # Save image
    result = response.json()
    image_bytes = base64.b64decode(result["artifacts"][0]["base64"])
    filename = f"scene_{scene_index}.png"
    
    with open(filename, "wb") as f:
        f.write(image_bytes)
    
    return filename

def generate_image_txt2img(scene_prompt, scene_index, stability_api_key):
    """Generate image using text-to-image (for group scenes)"""
    
    camera_angle = Config.CAMERA_PRESETS[scene_index % len(Config.CAMERA_PRESETS)]
    
    enhanced_prompt = f"""
    {scene_prompt}, {camera_angle},
    ancient Indian mythology, divine sacred setting,
    cinematic masterpiece, photorealistic, 8k uhd,
    epic lighting, volumetric rays, highly detailed
    """
    
    negative_prompt = """
    cartoon, anime, low quality, blurry, disfigured,
    modern objects, text, watermark
    """
    
    body = {
        "text_prompts": [
            {"text": enhanced_prompt, "weight": 1.0},
            {"text": negative_prompt, "weight": -1.0}
        ],
        "cfg_scale": 7,
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 35,
    }
    
    headers = {
        "Authorization": f"Bearer {stability_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(
        f"https://api.stability.ai/v1/generation/{Config.STABILITY_MODEL}/text-to-image",
        headers=headers,
        json=body,
        timeout=90
    )
    
    if response.status_code != 200:
        raise Exception(f"Stability AI error: {response.text}")
    
    result = response.json()
    image_bytes = base64.b64decode(result["artifacts"][0]["base64"])
    filename = f"scene_{scene_index}.png"
    
    with open(filename, "wb") as f:
        f.write(image_bytes)
    
    return filename