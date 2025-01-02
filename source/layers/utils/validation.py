import re
from PIL import Image
import os

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def validate_api_keys(gemini_key=None, eleven_labs_key=None):
    """Validate API keys format"""
    errors = []
    
    if gemini_key and not re.match(r'^[A-Za-z0-9-_]{39}$', gemini_key):
        errors.append("Invalid Gemini API key format")
        
    if eleven_labs_key and not re.match(r'^[A-Za-z0-9]{32}$', eleven_labs_key):
        errors.append("Invalid Eleven Labs API key format")
        
    return errors

def validate_content_type(content_type, valid_types):
    """Validate content type"""
    return content_type in valid_types

def validate_file_type(file_path, allowed_extensions):
    """Validate file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in allowed_extensions

def validate_image(image_path):
    """Validate image file"""
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except:
        return False

def validate_video_params(fps=None, duration=None):
    """Validate video parameters"""
    errors = []
    
    if fps is not None and not (isinstance(fps, int) and 1 <= fps <= 60):
        errors.append("FPS must be between 1 and 60")
        
    if duration is not None and not (isinstance(duration, (int, float)) and duration > 0):
        errors.append("Duration must be a positive number")
        
    return errors