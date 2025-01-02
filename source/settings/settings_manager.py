from typing import Any, Dict, Optional
from django.conf import settings as django_settings
from .service_settings import (
    AI_SETTINGS,
    RESOURCE_MONITOR_SETTINGS,
    CACHE_SETTINGS,
    CONTENT_SETTINGS,
    ASSET_SETTINGS,
    MONITORING_SETTINGS,
    VIDEO_SETTINGS,
    INTEGRATION_SETTINGS
)
import os

class SettingsManager:
    """Manages application settings with environment variable support"""
    
    def __init__(self):
        self._settings = {
            'ai': self._load_ai_settings(),
            'resource_monitor': RESOURCE_MONITOR_SETTINGS,
            'cache': CACHE_SETTINGS,
            'content': CONTENT_SETTINGS,
            'asset': ASSET_SETTINGS,
            'monitoring': MONITORING_SETTINGS,
            'video': self._load_video_settings(),
            'integration': INTEGRATION_SETTINGS
        }
    
    def _load_ai_settings(self) -> Dict[str, Any]:
        """Load AI settings with environment variables"""
        settings = AI_SETTINGS.copy()
        settings['gemini_key'] = os.getenv('GEMINI_KEY', '')
        settings['eleven_labs_key'] = os.getenv('ELEVEN_LABS_KEY', '')
        return settings
    
    def _load_video_settings(self) -> Dict[str, Any]:
        """Load video settings with environment variables"""
        settings = VIDEO_SETTINGS.copy()
        settings['ffmpeg_path'] = os.getenv('FFMPEG_PATH', None)
        return settings
    
    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        category_settings = self._settings.get(category, {})
        return category_settings.get(key, default)
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings for a category"""
        return self._settings.get(category, {}).copy()
    
    def get_monitoring_settings(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get_category('monitoring')
    
    def get_cache_timeout(self) -> int:
        """Get cache timeout setting"""
        return self.get_setting('cache', 'default_timeout', 3600)
    
    def get_batch_settings(self) -> Dict[str, Any]:
        """Get batch processing settings"""
        return {
            'max_batch_size': self.get_setting('content', 'max_batch_size'),
            'processing_timeout': self.get_setting('content', 'processing_timeout'),
            'max_retries': self.get_setting('content', 'max_retries')
        }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get resource monitoring limits"""
        return {
            'max_workers': self.get_setting('resource_monitor', 'max_workers'),
            'max_queue_size': self.get_setting('resource_monitor', 'max_queue_size'),
            'monitor_interval': self.get_setting('resource_monitor', 'monitor_interval')
        }
    
    def validate_file_size(self, size: int, file_type: str) -> bool:
        """Validate file size against settings"""
        max_size = self.get_setting('asset', 'max_file_size')
        return size <= max_size
    
    def validate_file_type(self, mime_type: str, asset_type: str) -> bool:
        """Validate file type against settings"""
        type_mapping = {
            'image': 'allowed_image_types',
            'audio': 'allowed_audio_types',
            'video': 'allowed_video_types'
        }
        allowed_types = self.get_setting('asset', type_mapping.get(asset_type, []))
        return mime_type in allowed_types
    
    def get_performance_thresholds(self) -> Dict[str, float]:
        """Get performance monitoring thresholds"""
        return {
            'performance': self.get_setting('monitoring', 'performance_threshold'),
            'alert': self.get_setting('monitoring', 'alert_threshold')
        }
    
    def get_integration_settings(self) -> Dict[str, Any]:
        """Get integration settings"""
        return self.get_category('integration')
    
    def get_video_settings(self) -> Dict[str, Any]:
        """Get video processing settings"""
        return self.get_category('video')
    
    def get_asset_settings(self) -> Dict[str, Any]:
        """Get asset processing settings"""
        return self.get_category('asset')

# Global settings manager instance
settings_manager = SettingsManager()
