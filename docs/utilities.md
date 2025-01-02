# Utility Documentation

## Video Generation Utility

### Features

- Professional transitions between clips
- Dynamic visual effects
- Text overlays and watermarks
- Audio synchronization
- High-quality encoding

### Effects

1. Transitions:
   - Cross fade
   - Fade to black
   - Slide transitions
   - Zoom transitions

2. Visual Effects:
   - Ken Burns effect (zoom)
   - Rotation
   - Noise overlay
   - Color grading

3. Text Effects:
   - Animated intros
   - Watermarks
   - Subtitles
   - Lower thirds

### Configuration

```python
# Video settings
MAX_VIDEO_SIZE = (1920, 1080)  # Full HD
VIDEO_FPS = 24
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'

# Effect settings
TRANSITION_DURATION = 1.0  # seconds
ZOOM_FACTOR = 1.3
NOISE_LEVEL = 0.03
```

### Example Usage

```python
# Create video with all effects
video_path = video_util.create_video(
    images=images,
    audio_path=audio_path,
    duration_per_image=4.0,
    transition_duration=1.0,
    add_effects=True
)

# Add custom intro
intro = video_util.create_intro(
    text="Welcome to My Channel",
    duration=3.0,
    background_color='black'
)

# Add watermark
final_video = video_util.add_watermark(
    video_path=video_path,
    watermark_text=" My Brand 2024"
)
```

## Image Processing Utility

### Features

- Image enhancement
- Professional filters
- Text overlays
- Optimization
- Batch processing

### Image Effects

1. Enhancement:
   - Brightness
   - Contrast
   - Sharpness
   - Color balance

2. Filters:
   - Blur
   - Sharpen
   - Edge enhance
   - Emboss
   - Smooth

3. Text:
   - Multiple positions
   - Custom fonts
   - Text outline
   - Opacity control

### Configuration

```python
# Image settings
MAX_IMAGE_SIZE = (1920, 1080)
JPEG_QUALITY = 95
CACHE_TIMEOUT = 3600  # 1 hour

# Enhancement defaults
DEFAULT_BRIGHTNESS = 1.1
DEFAULT_CONTRAST = 1.2
DEFAULT_SHARPNESS = 1.1
DEFAULT_COLOR = 1.2
```

### Example Usage

```python
# Process single image
processed = image_util.process_image(
    image=image,
    resize=True,
    enhance=True,
    filter_type='edge_enhance',
    text="My Caption",
    optimize=True
)

# Batch process images
processed_images = image_util.batch_process_images(
    images=images,
    resize=True,
    enhance=True,
    filter_type='sharpen'
)
```

## Document Processing Utility

### Document Processing Features

1. Document Optimization:
   - PDF compression and optimization
   - Word document image optimization
   - File size reduction
   - Quality preservation

2. Document Conversion:
   - PDF to Text
   - PDF to Word
   - Word to PDF
   - Format validation

3. Text Extraction:
   - Full text extraction from PDFs
   - Word document text extraction
   - Plain text handling
   - UTF-8 encoding support

4. Metadata Handling:
   - Document properties
   - Author information
   - Creation/modification dates
   - Page count and size
   - Revision tracking

### Document Configuration

```python
# Document settings
ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf'
}

DOCUMENT_EXTENSIONS = {
    '.txt',
    '.pdf',
    '.doc',
    '.docx',
    '.rtf'
}

# PDF optimization settings
PDF_IMAGE_QUALITY = 85
PDF_COMPRESSION = True
PDF_CLEANUP = True

# Word document settings
MAX_IMAGE_WIDTH = 6  # inches
WORD_COMPRESSION = True
```

### Document Processing Examples

```python
# Save and optimize document
doc_path = file_util.save_document(
    file_content=doc_content,
    filename="report.pdf",
    optimize=True
)

# Extract document text
text = file_util.extract_document_text(doc_path)

# Get document metadata
metadata = file_util.get_document_metadata(doc_path)
print(f"Author: {metadata['author']}")
print(f"Created: {metadata['created']}")
print(f"Pages: {metadata.get('page_count', 0)}")

# Convert document
pdf_path = file_util.convert_document(
    source_path="report.docx",
    target_format=".pdf"
)

# Create ZIP archive of documents
archive = file_util.create_zip_archive(
    files=document_files,
    output_filename="documents.zip"
)
```

### Document Best Practices

1. Optimization:
   ```python
   # Always optimize large documents
   if file_size > 5 * 1024 * 1024:  # 5MB
       doc_path = file_util.save_document(
           file_content=content,
           filename="large_doc.pdf",
           optimize=True
       )
   ```

2. Security:
   ```python
   # Validate document type
   if not file_util.validate_file_type(
       doc_path,
       file_util.ALLOWED_DOCUMENT_TYPES
   ):
       raise ValidationError("Invalid document type")
   ```

3. Metadata:
   ```python
   # Check document metadata
   metadata = file_util.get_document_metadata(doc_path)
   if metadata['size'] > max_size:
       logger.warning("Document exceeds size limit")
   ```

4. Conversion:
   ```python
   # Convert with error handling
   try:
       pdf_path = file_util.convert_document(
           source_path=doc_path,
           target_format=".pdf"
       )
   except Exception as e:
       logger.error(f"Conversion failed: {e}")
   ```

5. Cleanup:
   ```python
   # Clean temporary files
   file_util.clean_temp_files(
       max_age=timedelta(hours=1)
   )
   ```

## Advanced PDF Features

1. PDF Merging and Splitting:
   - Merge multiple PDFs
   - Split PDF into pages
   - Maintain quality
   - Optimize output

2. PDF Security:
   - Password protection
   - AES-256 encryption
   - Permission control
   - Secure deletion

3. PDF Optimization:
   - Image compression
   - DPI adjustment
   - Quality settings
   - Size reduction

4. PDF Watermarking:
   - Text watermarks
   - Custom positioning
   - Opacity control
   - Rotation options

### PDF Processing Examples

```python
# Merge PDFs
merged_pdf = file_util.merge_pdfs(
    pdf_files=["doc1.pdf", "doc2.pdf"],
    output_filename="merged.pdf"
)

# Split PDF
pages = file_util.split_pdf(
    pdf_file="document.pdf",
    output_dir="split_pages"
)

# Add watermark
watermarked = file_util.add_pdf_watermark(
    pdf_file="document.pdf",
    watermark_text="CONFIDENTIAL"
)

# Encrypt PDF
encrypted = file_util.encrypt_pdf(
    pdf_file="sensitive.pdf",
    user_password="user123",
    owner_password="admin456"
)

# Compress PDF
compressed = file_util.compress_pdf(
    pdf_file="large.pdf",
    quality="medium"  # 'low', 'medium', 'high'
)
```

### PDF Best Practices

1. Security:
   ```python
   # Always encrypt sensitive documents
   if is_sensitive:
       encrypted = file_util.encrypt_pdf(
           pdf_file=doc_path,
           user_password=user_pw,
           owner_password=admin_pw
       )
   ```

2. Optimization:
   ```python
   # Compress large PDFs
   if file_size > 10 * 1024 * 1024:  # 10MB
       compressed = file_util.compress_pdf(
           pdf_file=pdf_path,
           quality='medium'
       )
   ```

3. Watermarking:
   ```python
   # Add watermark to all pages
   watermarked = file_util.add_pdf_watermark(
       pdf_file=pdf_path,
       watermark_text=" Company 2024"
   )
   ```

4. Merging:
   ```python
   # Merge with validation
   if all(file_util.validate_file_type(f, {'.pdf'}) 
          for f in pdf_files):
       merged = file_util.merge_pdfs(
           pdf_files=pdf_files,
           output_filename="merged.pdf"
       )
   ```

5. Splitting:
   ```python
   # Split large documents
   if page_count > 50:
       pages = file_util.split_pdf(
           pdf_file=large_pdf,
           output_dir="chapters"
       )
   ```

## File Management Utility

### Features

- Secure file operations
- File type validation
- Organization
- Cleanup routines
- Archive creation

### File Types

```python
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
}

ALLOWED_VIDEO_TYPES = {
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo'
}

ALLOWED_AUDIO_TYPES = {
    'audio/mpeg',
    'audio/wav',
    'audio/ogg'
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf'
}

DOCUMENT_EXTENSIONS = {
    '.txt',
    '.pdf',
    '.doc',
    '.docx',
    '.rtf'
}
```

### Directory Structure

```
media/
├── images/
│   ├── original/
│   ├── processed/
│   └── thumbnails/
├── videos/
│   ├── final/
│   └── temp/
├── audio/
│   ├── voiceover/
│   └── music/
├── documents/
│   ├── pdf/
│   ├── word/
│   └── text/
└── temp/
```

### Example Usage

```python
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

# Organize files
organized = file_util.organize_files(
    directory=media_dir,
    organize_by='type'
)

# Save document with organization
doc_path = file_util.save_file(
    file_content=doc_content,
    filename="report.pdf",
    category="documents/pdf"
)

# Validate document type
is_valid = file_util.validate_file_type(
    doc_path,
    file_util.ALLOWED_DOCUMENT_TYPES
)

# Create ZIP archive of documents
archive = file_util.create_zip_archive(
    files=document_files,
    output_filename="documents.zip"
)

# Organize documents
organized = file_util.organize_files(
    directory=docs_dir,
    organize_by='type'
)
```

## Best Practices

### Performance

1. Use caching:
   ```python
   from django.core.cache import cache

   cache_key = f"image_search_{query}"
   cached_result = cache.get(cache_key)
   if cached_result:
       return cached_result
   ```

2. Clean temporary files:
   ```python
   file_util.clean_temp_files(
       max_age=timedelta(hours=24)
   )
   ```

3. Optimize file sizes:
   ```python
   image_util.optimize_image(
       image,
       quality=85
   )
   ```

### Security

1. Validate file types:
   ```python
   if not file_util.validate_file_type(
       file_path,
       file_util.ALLOWED_VIDEO_TYPES
   ):
       raise ValidationError("Invalid file type")
   ```

2. Use secure deletion:
   ```python
   file_util.delete_file(
       file_path,
       secure=True
   )
   ```

3. Generate safe filenames:
   ```python
   safe_name = file_util.generate_unique_filename(
       original_name,
       directory
   )
   ```

### Error Handling

1. Use try-except blocks:
   ```python
   try:
       result = operation()
   except Exception as e:
       self.add_error(f"Operation failed: {str(e)}")
       return None
   ```

2. Log errors:
   ```python
   logger.error(
       f"Failed to process file: {str(e)}",
       exc_info=True
   )
   ```

3. Validate input:
   ```python
   if not self.validate({'file': file}):
       return None
   ```

### Memory Management

1. Use context managers:
   ```python
   with tempfile.TemporaryDirectory() as temp_dir:
       # Process files
       pass  # Cleanup is automatic
   ```

2. Stream large files:
   ```python
   with open(file_path, 'wb') as f:
       for chunk in file.chunks():
           f.write(chunk)
   ```

3. Clean up resources:
   ```python
   try:
       # Process file
       pass
   finally:
       if os.path.exists(temp_file):
           os.remove(temp_file)
   ```
