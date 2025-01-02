import os
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from io import BytesIO
from typing import List, Optional, Tuple, Dict, Any
import logging
from apps.core.services import BaseService
from django.core.exceptions import ValidationError
from django.core.cache import cache
import json
import numpy as np
from django.conf import settings
import tempfile

logger = logging.getLogger(__name__)

class ImageProcessingUtility(BaseService):
    """Utility for processing and enhancing images"""

    def __init__(self):
        super().__init__()
        self.cache_timeout = 3600  # 1 hour cache
        self.max_image_size = (1920, 1080)  # Full HD
        self.quality = 95  # High quality JPEG
        
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate input data"""
        if 'image' not in data and 'image_path' not in data:
            raise ValidationError("Image or image path is required")

    def enhance_image(self, image: Image.Image, 
                     brightness: float = 1.1,
                     contrast: float = 1.2,
                     sharpness: float = 1.1,
                     color: float = 1.2) -> Image.Image:
        """Enhance image with professional adjustments"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply enhancements
            image = ImageEnhance.Brightness(image).enhance(brightness)
            image = ImageEnhance.Contrast(image).enhance(contrast)
            image = ImageEnhance.Sharpness(image).enhance(sharpness)
            image = ImageEnhance.Color(image).enhance(color)
            
            return image
        except Exception as e:
            self.add_error(f"Failed to enhance image: {str(e)}")
            return image

    def apply_filter(self, image: Image.Image, filter_type: str) -> Image.Image:
        """Apply artistic filters to image"""
        try:
            filters = {
                'blur': ImageFilter.GaussianBlur(2),
                'sharpen': ImageFilter.SHARPEN,
                'edge_enhance': ImageFilter.EDGE_ENHANCE,
                'emboss': ImageFilter.EMBOSS,
                'smooth': ImageFilter.SMOOTH
            }
            
            if filter_type in filters:
                return image.filter(filters[filter_type])
            else:
                self.add_error(f"Unknown filter type: {filter_type}")
                return image
        except Exception as e:
            self.add_error(f"Failed to apply filter: {str(e)}")
            return image

    def resize_image(self, image: Image.Image, 
                    size: Optional[Tuple[int, int]] = None,
                    maintain_aspect: bool = True) -> Image.Image:
        """Resize image with aspect ratio preservation"""
        try:
            if not size:
                size = self.max_image_size
                
            if maintain_aspect:
                image.thumbnail(size, Image.Resampling.LANCZOS)
                return image
            else:
                return image.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            self.add_error(f"Failed to resize image: {str(e)}")
            return image

    def add_text_overlay(self, image: Image.Image, 
                        text: str,
                        position: str = 'bottom',
                        font_size: int = 30,
                        color: str = 'white',
                        outline_color: str = 'black') -> Image.Image:
        """Add text overlay to image with outline"""
        try:
            # Create drawing context
            draw = ImageDraw.Draw(image)
            
            # Load font (use default if custom font not available)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size and position
            text_width, text_height = draw.textsize(text, font=font)
            x = (image.width - text_width) // 2
            
            if position == 'bottom':
                y = image.height - text_height - 20
            elif position == 'top':
                y = 20
            else:
                y = (image.height - text_height) // 2
            
            # Draw text outline
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    draw.text((x+adj, y+adj2), text, font=font, fill=outline_color)
            
            # Draw main text
            draw.text((x, y), text, font=font, fill=color)
            
            return image
        except Exception as e:
            self.add_error(f"Failed to add text overlay: {str(e)}")
            return image

    def create_thumbnail(self, image: Image.Image, 
                        size: Tuple[int, int] = (320, 180)) -> Image.Image:
        """Create thumbnail with proper scaling"""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            return thumbnail
        except Exception as e:
            self.add_error(f"Failed to create thumbnail: {str(e)}")
            return image

    def optimize_image(self, image: Image.Image, 
                      quality: Optional[int] = None) -> Image.Image:
        """Optimize image for web delivery"""
        try:
            if not quality:
                quality = self.quality
                
            # Create temporary buffer
            buffer = BytesIO()
            
            # Save with optimization
            image.save(buffer, format='JPEG', 
                      quality=quality, 
                      optimize=True)
            
            # Return new image from buffer
            buffer.seek(0)
            return Image.open(buffer)
        except Exception as e:
            self.add_error(f"Failed to optimize image: {str(e)}")
            return image

    def download_images(self, query: str, num_images: int = 5) -> List[Image.Image]:
        """Download images from Bing with caching"""
        try:
            # Check cache first
            cache_key = f"image_search_{query}_{num_images}"
            cached_results = cache.get(cache_key)
            
            if cached_results:
                logger.info(f"Using cached images for query: {query}")
                return cached_results

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            search_url = f"https://www.bing.com/images/search?q={query}&count={num_images}"
            response = requests.get(search_url, headers=headers)
            
            # Extract image URLs
            image_urls = []
            start = 0
            while len(image_urls) < num_images:
                url_start = response.text.find('murl&quot;:&quot;', start)
                if url_start == -1:
                    break
                    
                url_end = response.text.find('&quot;', url_start + 20)
                if url_end == -1:
                    break
                    
                image_url = response.text[url_start + 18:url_end]
                image_urls.append(image_url)
                start = url_end + 1

            # Download and process images
            images = []
            for url in image_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        
                        # Process image
                        img = self.resize_image(img)
                        img = self.enhance_image(img)
                        img = self.optimize_image(img)
                        
                        images.append(img)
                except Exception as e:
                    logger.error(f"Failed to download image from {url}: {str(e)}")
                    continue

            # Cache results
            if images:
                cache.set(cache_key, images, self.cache_timeout)

            return images
        except Exception as e:
            self.add_error(f"Failed to download images: {str(e)}")
            return []

    def process_image(self, image: Image.Image,
                     resize: bool = True,
                     enhance: bool = True,
                     filter_type: Optional[str] = None,
                     text: Optional[str] = None,
                     optimize: bool = True) -> Image.Image:
        """Process image with multiple effects"""
        try:
            if not self.validate({'image': image}):
                return image
                
            # Apply processing steps
            if resize:
                image = self.resize_image(image)
                
            if enhance:
                image = self.enhance_image(image)
                
            if filter_type:
                image = self.apply_filter(image, filter_type)
                
            if text:
                image = self.add_text_overlay(image, text)
                
            if optimize:
                image = self.optimize_image(image)
                
            return image
        except Exception as e:
            self.add_error(f"Failed to process image: {str(e)}")
            return image

    def batch_process_images(self, images: List[Image.Image], 
                           **process_args) -> List[Image.Image]:
        """Process multiple images with the same settings"""
        processed_images = []
        for image in images:
            processed = self.process_image(image, **process_args)
            processed_images.append(processed)
        return processed_images