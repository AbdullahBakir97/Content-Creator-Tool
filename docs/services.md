# Service Documentation

## Content Creation Service

The `ContentCreationService` manages the complete content creation workflow.

### Usage

```python
from source.apps.content.services import ContentCreationService

service = ContentCreationService(
    gemini_key="your-gemini-key",
    eleven_labs_key="your-eleven-labs-key",
    ffmpeg_path="/path/to/ffmpeg"
)

# Create complete content
content = service.create_content(
    content_type="tutorial",
    title="How to Code in Python",
    watermark="My Channel",
    intro_text="Welcome to this Tutorial",
    add_effects=True
)

# Check content status
status = service.get_content_status(content.id)
```

### Methods

#### create_content
Creates complete content including script, voiceover, and video.

**Parameters:**
- `content_type` (str): Type of content to generate
- `title` (str): Content title
- `watermark` (Optional[str]): Watermark text
- `intro_text` (Optional[str]): Intro text
- `add_effects` (bool): Add video effects

**Returns:**
- `Content`: Created content object or None if failed

#### get_content_status
Get status and details of content creation process.

**Parameters:**
- `content_id` (int): Content ID

**Returns:**
- `Dict[str, Any]`: Content status information

## Video Generation Utility

The `VideoGenerationUtility` handles video creation with professional effects.

### Usage

```python
from source.layers.utils.video_generation import VideoGenerationUtility

video_util = VideoGenerationUtility(ffmpeg_path="/path/to/ffmpeg")

# Create video with effects
video_path = video_util.create_video(
    images=images,
    audio_path="audio.mp3",
    add_effects=True
)

# Add watermark
watermarked = video_util.add_watermark(
    video_path=video_path,
    watermark_text="My Brand"
)
```

### Methods

#### create_video
Create professional video from images with effects and transitions.

**Parameters:**
- `images` (List[Image.Image]): List of PIL images
- `audio_path` (Optional[str]): Path to audio file
- `output_path` (Optional[str]): Output path
- `duration_per_image` (float): Duration for each image
- `transition_duration` (float): Duration of transitions
- `add_effects` (bool): Add visual effects

**Returns:**
- `Optional[str]`: Path to created video

#### add_watermark
Add watermark to video.

**Parameters:**
- `video_path` (str): Input video path
- `watermark_text` (str): Watermark text
- `output_path` (Optional[str]): Output path

**Returns:**
- `Optional[str]`: Path to watermarked video

## Image Processing Utility

The `ImageProcessingUtility` handles image processing and enhancement.

### Usage

```python
from source.layers.utils.image_processing import ImageProcessingUtility

image_util = ImageProcessingUtility()

# Process image with effects
processed = image_util.process_image(
    image=image,
    resize=True,
    enhance=True,
    filter_type='edge_enhance',
    text="My Caption"
)

# Batch process images
processed_images = image_util.batch_process_images(
    images=images,
    **process_args
)
```

### Methods

#### process_image
Process image with multiple effects.

**Parameters:**
- `image` (Image.Image): PIL Image
- `resize` (bool): Resize image
- `enhance` (bool): Enhance image
- `filter_type` (Optional[str]): Filter to apply
- `text` (Optional[str]): Text overlay
- `optimize` (bool): Optimize for web

**Returns:**
- `Image.Image`: Processed image

#### batch_process_images
Process multiple images with the same settings.

**Parameters:**
- `images` (List[Image.Image]): List of PIL images
- `**process_args`: Arguments for process_image

**Returns:**
- `List[Image.Image]`: Processed images

## File Management Utility

The `FileManagementUtility` handles file operations and organization.

### Usage

```python
from source.layers.utils.file_management import FileManagementUtility

file_util = FileManagementUtility()

# Save file with organization
file_path = file_util.save_file(
    file_content=content,
    filename="video.mp4",
    category="videos"
)

# Create ZIP archive
archive = file_util.create_zip_archive(
    files=files,
    output_filename="content.zip"
)
```

### Methods

#### save_file
Save file with proper organization.

**Parameters:**
- `file_content` (Union[bytes, Image.Image]): File content
- `filename` (str): Target filename
- `directory` (Optional[str]): Target directory
- `category` (str): File category

**Returns:**
- `Optional[str]`: Saved file path

#### create_zip_archive
Create ZIP archive from files.

**Parameters:**
- `files` (List[str]): List of file paths
- `output_filename` (str): Output filename
- `base_dir` (Optional[str]): Base directory

**Returns:**
- `Optional[str]`: Created archive path

## Error Handling

All services extend `BaseService` which provides:

```python
def add_error(self, error: str) -> None:
    """Add error message"""

def has_errors(self) -> bool:
    """Check if service has errors"""

def get_errors(self) -> List[str]:
    """Get all error messages"""

def clear_errors(self) -> None:
    """Clear all error messages"""
```

Example error handling:

```python
result = service.some_operation()
if service.has_errors():
    errors = service.get_errors()
    logger.error(f"Operation failed: {errors}")
```

## Logging

Services use Python's logging module:

```python
import logging
logger = logging.getLogger(__name__)

# Log levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

Configure logging in settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'source': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
