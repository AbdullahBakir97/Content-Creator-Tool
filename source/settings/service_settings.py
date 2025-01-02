"""Service configuration settings"""

# AI Service Settings
AI_SETTINGS = {
    'gemini_key': 'AIzaSyDIZbHAyU-2lH9YqhEYMJov0KTRoV9bdFg',  # Set via environment variable
    'eleven_labs_key': 'sk_9597a32354675d981372ca04e646ad0827d42c94df4ff575',  # Set via environment variable
    'max_retries': 3,
    'timeout': 30,
    'batch_size': 10
}

# Resource Monitor Settings
RESOURCE_MONITOR_SETTINGS = {
    'max_workers': 4,
    'max_queue_size': 100,
    'monitor_interval': 5  # seconds
}

# Cache Settings
CACHE_SETTINGS = {
    'default_timeout': 3600,
    'max_entries': 1000,
    'version': 1
}

# Content Processing Settings
CONTENT_SETTINGS = {
    'max_batch_size': 50,
    'processing_timeout': 300,  # seconds
    'max_retries': 3,
    'chunk_size': 1024 * 1024  # 1MB
}

# Asset Processing Settings
ASSET_SETTINGS = {
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'allowed_image_types': ['image/jpeg', 'image/png', 'image/gif'],
    'allowed_audio_types': ['audio/mpeg', 'audio/wav'],
    'allowed_video_types': ['video/mp4', 'video/quicktime'],
    'image_max_dimension': 4096,
    'video_max_duration': 3600,  # 1 hour
    'audio_max_duration': 3600  # 1 hour
}

# Monitoring Settings
MONITORING_SETTINGS = {
    'enabled': True,
    'log_level': 'INFO',
    'metrics_retention_days': 7,
    'performance_threshold': 1.0,  # seconds
    'alert_threshold': 5.0  # seconds
}

# Video Processing Settings
VIDEO_SETTINGS = {
    'ffmpeg_path': None,  # Set via environment variable
    'default_resolution': '1080p',
    'default_framerate': 30,
    'default_bitrate': '4M'
}

# Service Integration Settings
INTEGRATION_SETTINGS = {
    'max_concurrent_requests': 10,
    'request_timeout': 30,
    'retry_delay': 1,
    'circuit_breaker_threshold': 5
}
