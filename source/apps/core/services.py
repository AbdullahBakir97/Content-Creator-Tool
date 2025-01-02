from .models import Setting
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from django.core.exceptions import ValidationError
from django.core.cache import cache
from datetime import datetime
import json
import traceback

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ServiceResult(Generic[T]):
    """Generic result wrapper for service operations"""
    
    def __init__(self, success: bool, data: Optional[T] = None, 
                 error: Optional[str] = None, error_details: Optional[Dict] = None):
        self.success = success
        self.data = data
        self.error = error
        self.error_details = error_details or {}
        self.timestamp = datetime.now()

    @property
    def failed(self) -> bool:
        return not self.success

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'error_details': self.error_details,
            'timestamp': self.timestamp.isoformat()
        }

class BaseService(ABC):
    """Enhanced base service class with advanced functionality"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self._cache_prefix = self.__class__.__name__
        
    def add_error(self, error: str, error_type: str = 'general', 
                 details: Optional[Dict] = None) -> None:
        """Add detailed error information"""
        error_info = {
            'message': error,
            'type': error_type,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc(),
            'details': details or {}
        }
        self.errors.append(error_info)
        logger.error(f"Service error: {json.dumps(error_info)}")
        
    def has_errors(self) -> bool:
        return bool(self.errors)
        
    def get_errors(self) -> List[Dict[str, Any]]:
        return self.errors
        
    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """Get the most recent error"""
        return self.errors[-1] if self.errors else None
        
    def clear_errors(self) -> None:
        self.errors = []

    def validate(self, data: Dict[str, Any]) -> ServiceResult[bool]:
        """Enhanced validation with detailed results"""
        try:
            self._validate(data)
            return ServiceResult(True, True)
        except ValidationError as e:
            self.add_error(str(e), 'validation_error', {'fields': data.keys()})
            return ServiceResult(False, False, str(e), {'validation_errors': e.message_dict})
        except Exception as e:
            self.add_error(str(e), 'validation_error')
            return ServiceResult(False, False, str(e))
            
    @abstractmethod
    def _validate(self, data: Dict[str, Any]) -> None:
        pass

    def get_cached(self, key: str, default: Any = None) -> Any:
        """Get cached value with service-specific prefix"""
        full_key = f"{self._cache_prefix}:{key}"
        return cache.get(full_key, default)

    def set_cached(self, key: str, value: Any, timeout: int = 3600) -> None:
        """Set cached value with service-specific prefix"""
        full_key = f"{self._cache_prefix}:{key}"
        cache.set(full_key, value, timeout)

    def clear_cached(self, key: str) -> None:
        """Clear cached value"""
        full_key = f"{self._cache_prefix}:{key}"
        cache.delete(full_key)

class SettingsService(BaseService):
    """Enhanced settings management service"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> ServiceResult[Any]:
        """Get setting with caching"""
        try:
            cache_key = f"setting:{key}"
            value = cache.get(cache_key)
            
            if value is None:
                value = Setting.get_setting(key)
                if value is not None:
                    cache.set(cache_key, value, cls.CACHE_TIMEOUT)
                    
            return ServiceResult(True, value or default)
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {str(e)}")
            return ServiceResult(False, default, str(e))

    @classmethod
    def update_setting(cls, key: str, value: Any) -> ServiceResult[bool]:
        """Update setting with validation"""
        try:
            Setting.update_setting(key, value)
            cache_key = f"setting:{key}"
            cache.delete(cache_key)
            return ServiceResult(True, True)
        except Exception as e:
            logger.error(f"Failed to update setting {key}: {str(e)}")
            return ServiceResult(False, False, str(e))

    @classmethod
    def load_default_settings(cls) -> ServiceResult[Dict[str, Any]]:
        """Load default settings with validation"""
        try:
            defaults = {
                'content_generation': {
                    'max_retries': 3,
                    'timeout': 30,
                    'batch_size': 5
                },
                'voiceover': {
                    'default_voice': 'en-US-Standard-A',
                    'quality': 'high'
                },
                'file_management': {
                    'max_file_size': 100 * 1024 * 1024,  # 100MB
                    'allowed_extensions': ['.mp4', '.mp3', '.wav', '.pdf']
                }
            }
            
            results = {}
            for category, settings in defaults.items():
                for key, value in settings.items():
                    setting_key = f"{category}.{key}"
                    result = cls.update_setting(setting_key, value)
                    results[setting_key] = result.success
                    
            return ServiceResult(True, results)
        except Exception as e:
            logger.error(f"Failed to load default settings: {str(e)}")
            return ServiceResult(False, None, str(e))

class LoggingService(BaseService):
    """Enhanced logging service with structured logging"""
    
    @classmethod
    def log(cls, level: str, message: str, 
            extra: Optional[Dict[str, Any]] = None,
            exc_info: bool = False) -> None:
        """Structured logging with context"""
        try:
            log_data = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'context': extra or {},
            }
            
            if exc_info:
                log_data['traceback'] = traceback.format_exc()
            
            getattr(logger, level.lower())(
                json.dumps(log_data),
                extra={'structured': True},
                exc_info=exc_info
            )
        except Exception as e:
            logger.error(f"Logging failed: {str(e)}")

    @classmethod
    def log_info(cls, message: str, **kwargs) -> None:
        cls.log('INFO', message, **kwargs)

    @classmethod
    def log_warning(cls, message: str, **kwargs) -> None:
        cls.log('WARNING', message, **kwargs)

    @classmethod
    def log_error(cls, message: str, **kwargs) -> None:
        cls.log('ERROR', message, exc_info=True, **kwargs)

    @classmethod
    def log_critical(cls, message: str, **kwargs) -> None:
        cls.log('CRITICAL', message, exc_info=True, **kwargs)