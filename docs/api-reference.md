# API Reference

## Content Creation API

### Content Generation

#### Generate Content
```python
POST /api/content/generate/
```

Generate complete content including script, voiceover, and video.

**Parameters:**
- `content_type` (string): Type of content to generate
- `title` (string): Content title
- `watermark` (string, optional): Watermark text
- `intro_text` (string, optional): Intro text
- `add_effects` (boolean, optional): Add video effects

**Response:**
```json
{
    "id": "content_id",
    "title": "Content Title",
    "status": "completed",
    "script": "Generated script...",
    "assets": [
        {
            "type": "video",
            "path": "/media/videos/final_video.mp4"
        },
        {
            "type": "audio",
            "path": "/media/audio/voiceover.mp3"
        }
    ]
}
```

#### Get Content Status
```python
GET /api/content/{content_id}/status/
```

Get the status of content generation.

**Response:**
```json
{
    "id": "content_id",
    "status": "processing",
    "progress": 75,
    "errors": []
}
```

### Video Generation

#### Create Video
```python
POST /api/video/create/
```

Create a video from images and audio.

**Parameters:**
- `images` (array): List of image files
- `audio` (file, optional): Audio file
- `effects` (object, optional): Video effect settings
- `watermark` (string, optional): Watermark text

**Response:**
```json
{
    "video_path": "/media/videos/output.mp4",
    "duration": 120,
    "size": 1024576
}
```

### Image Processing

#### Process Image
```python
POST /api/image/process/
```

Process an image with effects.

**Parameters:**
- `image` (file): Image file
- `resize` (boolean, optional): Resize image
- `enhance` (boolean, optional): Enhance image
- `filter_type` (string, optional): Filter to apply
- `text` (string, optional): Text overlay
- `optimize` (boolean, optional): Optimize for web

**Response:**
```json
{
    "image_path": "/media/images/processed.jpg",
    "dimensions": [1920, 1080],
    "size": 102400
}
```

## Error Handling

All API endpoints follow consistent error handling:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description",
        "details": {
            "field": "Additional information"
        }
    }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input parameters
- `PROCESSING_ERROR`: Error during content processing
- `NOT_FOUND`: Requested resource not found
- `PERMISSION_DENIED`: Insufficient permissions

## Rate Limiting

API endpoints are rate-limited:
- 100 requests per minute for authenticated users
- 10 requests per minute for anonymous users

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1577836800
```

## Authentication

API requires authentication using JWT tokens:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

Get token:
```python
POST /api/token/
{
    "username": "user",
    "password": "pass"
}
```

Refresh token:
```python
POST /api/token/refresh/
{
    "refresh": "refresh_token"
}
```

## Webhooks

Subscribe to content generation events:

```python
POST /api/webhooks/subscribe/
{
    "url": "https://your-domain.com/webhook",
    "events": ["content.completed", "content.failed"]
}
```

Webhook payload:
```json
{
    "event": "content.completed",
    "content_id": "content_id",
    "timestamp": "2024-01-01T12:00:00Z",
    "data": {
        "status": "completed",
        "assets": []
    }
}
```
