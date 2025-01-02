import os
import numpy as np
from typing import List, Optional, Dict, Any
import logging
from apps.core.services import BaseService
from django.core.exceptions import ValidationError
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips, 
    CompositeVideoClip, VideoFileClip, TextClip, ColorClip
)
from moviepy.video.fx import all as vfx
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)

class VideoGenerationUtility(BaseService):
    """Utility for generating professional videos with effects"""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        super().__init__()
        if ffmpeg_path:
            os.environ["IMAGEMAGICK_BINARY"] = ffmpeg_path

    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate input data"""
        if 'images' not in data:
            raise ValidationError("Images are required for video generation")
        if not data['images']:
            raise ValidationError("At least one image is required")

    def add_noise_effect(self, clip, noise_level: float = 0.05):
        """Add noise effect to video clip"""
        try:
            def make_frame(t):
                frame = clip.get_frame(t)
                noise = np.random.normal(scale=255 * noise_level, size=frame.shape).astype('uint8')
                noisy_frame = np.clip(frame + noise, 0, 255).astype('uint8')
                return noisy_frame
            return clip.fl(make_frame)
        except Exception as e:
            self.add_error(f"Failed to add noise effect: {str(e)}")
            return clip

    def create_transition(self, clip1, clip2, transition_duration: float = 1.0):
        """Create smooth transition between clips"""
        try:
            end_clip = clip1.crossfadeout(transition_duration)
            start_clip = clip2.crossfadein(transition_duration)
            return concatenate_videoclips([end_clip, start_clip])
        except Exception as e:
            self.add_error(f"Failed to create transition: {str(e)}")
            return concatenate_videoclips([clip1, clip2])

    def add_text_overlay(self, clip, text: str, duration: float, 
                        position: str = 'bottom', fontsize: int = 30):
        """Add text overlay to video clip"""
        try:
            text_clip = TextClip(text, fontsize=fontsize, color='white', font='Arial')
            text_clip = text_clip.set_duration(duration)
            
            # Position text
            if position == 'bottom':
                text_clip = text_clip.set_position(('center', 'bottom'))
            elif position == 'top':
                text_clip = text_clip.set_position(('center', 'top'))
            else:
                text_clip = text_clip.set_position('center')

            return CompositeVideoClip([clip, text_clip])
        except Exception as e:
            self.add_error(f"Failed to add text overlay: {str(e)}")
            return clip

    def create_video(self, images: List[Image.Image], audio_path: Optional[str] = None, 
                    output_path: Optional[str] = None, duration_per_image: float = 4.0,
                    transition_duration: float = 1.0, add_effects: bool = True) -> Optional[str]:
        """Create professional video from images with effects and transitions"""
        try:
            if not self.validate({'images': images}):
                return None

            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                video_clips = []
                
                # Process each image
                for i, img in enumerate(images):
                    # Save image temporarily
                    temp_img_path = os.path.join(temp_dir, f"image_{i}.jpg")
                    img.save(temp_img_path, "JPEG")
                    
                    # Create clip from image
                    clip = ImageClip(temp_img_path).set_duration(duration_per_image)
                    
                    # Add effects if requested
                    if add_effects:
                        # Add zoom effect
                        clip = clip.fx(vfx.zoom, 1.3, duration_per_image)
                        
                        # Add slight rotation
                        clip = clip.fx(vfx.rotate, lambda t: 3 * np.sin(t))
                        
                        # Add noise effect
                        clip = self.add_noise_effect(clip, 0.03)
                    
                    video_clips.append(clip)

                # Create transitions between clips
                final_clips = []
                for i in range(len(video_clips)):
                    if i > 0:
                        # Create transition between current and previous clip
                        transition = self.create_transition(
                            video_clips[i-1], 
                            video_clips[i], 
                            transition_duration
                        )
                        final_clips.append(transition)
                    else:
                        final_clips.append(video_clips[i])

                # Concatenate all clips
                final_video = concatenate_videoclips(final_clips, method="compose")
                
                # Add audio if provided
                if audio_path and os.path.exists(audio_path):
                    audio_clip = AudioFileClip(audio_path)
                    final_video = final_video.set_audio(audio_clip)
                    
                    # Adjust video duration to match audio
                    final_video = final_video.set_duration(audio_clip.duration)

                # Generate output path if not provided
                if not output_path:
                    output_path = os.path.join(temp_dir, "output.mp4")

                # Write final video
                final_video.write_videofile(
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"),
                    remove_temp=True
                )

                logger.info(f"Video generated successfully: {output_path}")
                return output_path

        except Exception as e:
            self.add_error(f"Failed to generate video: {str(e)}")
            return None

    def add_watermark(self, video_path: str, watermark_text: str, 
                     output_path: Optional[str] = None) -> Optional[str]:
        """Add watermark to video"""
        try:
            video = VideoFileClip(video_path)
            
            # Create watermark text clip
            watermark = (TextClip(watermark_text, fontsize=30, color='white', font='Arial')
                        .set_duration(video.duration)
                        .set_position(('right', 'bottom'))
                        .set_opacity(0.5))
            
            # Composite video with watermark
            final_video = CompositeVideoClip([video, watermark])
            
            # Generate output path if not provided
            if not output_path:
                output_path = os.path.splitext(video_path)[0] + "_watermarked.mp4"
            
            # Write final video
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            return output_path
        except Exception as e:
            self.add_error(f"Failed to add watermark: {str(e)}")
            return None

    def create_intro(self, text: str, duration: float = 3.0, 
                    background_color: str = 'black') -> Optional[VideoClip]:
        """Create intro clip with text animation"""
        try:
            # Create background
            bg_clip = ColorClip((1920, 1080), col=background_color).set_duration(duration)
            
            # Create text clip with fade in effect
            txt_clip = (TextClip(text, fontsize=70, color='white', font='Arial')
                       .set_position('center')
                       .set_duration(duration)
                       .crossfadein(1.0))
            
            # Composite clips
            intro = CompositeVideoClip([bg_clip, txt_clip])
            return intro
        except Exception as e:
            self.add_error(f"Failed to create intro: {str(e)}")
            return None
