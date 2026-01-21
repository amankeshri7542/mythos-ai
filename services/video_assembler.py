# =========================================================
# Video Assembler Service
# =========================================================

import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap
from config import Config

def add_subtitles_to_image(image_path, text):
    """
    Adds text subtitles to the bottom of an image using Pillow.
    Returns the path to the modified image.
    """
    try:
        img = Image.open(image_path)
        
        # Font configuration
        # Try to use a nice font, fallback to default
        try:
            # Common paths for fonts on standard systems
            font_path = "Arial" # Default for many systems if handled by PIL
            if os.name == 'posix': # macOS/Linux
                if os.path.exists("/System/Library/Fonts/Supplemental/Arial.ttf"):
                    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
                elif os.path.exists("/Library/Fonts/Arial.ttf"):
                    font_path = "/Library/Fonts/Arial.ttf"
                elif os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            
            font = ImageFont.truetype(font_path, Config.SUBTITLE_FONT_SIZE)
        except Exception:
            font = ImageFont.load_default()
            
        # Wrap text
        lines = textwrap.wrap(text, width=Config.SUBTITLE_MAX_WIDTH)
        
        # Calculate text height and position
        # Get line height using getbbox (more accurate than getsize)
        try:
            left, top, right, bottom = font.getbbox("Ay")
            line_height = bottom - top + 15 # Add some padding
        except AttributeError:
             # Fallback for older Pillow versions just in case
            line_height = Config.SUBTITLE_FONT_SIZE + 15

        total_text_height = len(lines) * line_height
        
        # Position at the bottom with some padding
        image_width, image_height = img.size
        y_text = image_height - total_text_height - 50
        
        # Draw background for text (optional but good for readability)
        # Semi-transparent black box
        box_coords = [
            (0, y_text - 10),
            (image_width, image_height - 20)
        ]
        
        # To draw with alpha, we need an RGBA image
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(box_coords, fill=(0, 0, 0, 160))
        
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img) # Re-create draw object for RGB image
        
        # Draw text
        for line in lines:
            # Center text
            try:
                # textbbox is available in newer Pillow versions
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
            except AttributeError:
                 # Fallback
                 text_width = draw.textlength(line, font=font)

            x_text = (image_width - text_width) / 2
            
            # Draw with shadow/outline for better visibility
            shadow_color = (0, 0, 0)
            text_color = (255, 255, 255)
            
            # Simple shadow
            draw.text((x_text + 2, y_text + 2), line, font=font, fill=shadow_color)
            draw.text((x_text, y_text), line, font=font, fill=text_color)
            
            y_text += line_height
            
        # Save output
        output_path = f"sub_{os.path.basename(image_path)}"
        img.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"Error adding subtitles: {e}")
        return image_path

def create_video_clip(image_path, audio_path):
    """
    Creates a video clip from an image and audio file.
    Returns a moviepy VideoClip object.
    """
    try:
        audio = AudioFileClip(audio_path)
        video = ImageClip(image_path)
        
        # Set duration to match audio (MoviePy v2 uses with_ prefix)
        video = video.with_duration(audio.duration)
        video = video.with_audio(audio)
        video = video.with_fps(24)
        
        return video
    except Exception as e:
        raise Exception(f"Failed to create video clip: {str(e)}")

def assemble_final_video(clips, output_filename="final_video.mp4"):
    """
    Concatenates clips into a final video.
    Returns the path to the output video.
    """
    try:
        if not clips:
            raise ValueError("No clips provided to assemble")
            
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_filename, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            logger=None # Reduce console spam
        )
        
        # Close clips to release resources
        try:
            for clip in clips:
                clip.close()
            final_clip.close()
        except:
            pass
            
        return output_filename
    except Exception as e:
        raise Exception(f"Failed to assemble final video: {str(e)}")
