from typing import Optional, Any, Dict
from django.core.cache import cache
from source.layers.middleware.monitoring import (
    PerformanceMonitor,
    MetricsCollector
)
from source.apps.core.services import BaseService, ServiceResult

class CacheManager(BaseService):
    """Manages caching operations with monitoring"""
    
    def __init__(self, settings, performance_monitor: PerformanceMonitor, **kwargs):
        super().__init__()
        self.settings = settings
        self.performance_monitor = performance_monitor
        self.default_timeout = self.settings.get_cache_timeout()
        self.metrics_collector = MetricsCollector(
            settings=self.settings.get_monitoring_settings()
        )
        
    @property
    def monitor(self):
        """Get performance monitor decorator"""
        return self.performance_monitor.monitor
        
    async def get_or_create(self, key: str, creator_func, timeout: Optional[int] = None) -> ServiceResult:
        """Get from cache or create with monitoring"""
        return await self.monitor("cache_operation")(self._get_or_create)(key, creator_func, timeout)
    
    async def _get_or_create(self, key: str, creator_func, timeout: Optional[int] = None) -> ServiceResult:
        """Internal method to get or create cache entry"""
        try:
            value = cache.get(key)
            if not value:
                value = await creator_func()
                cache.set(key, value, timeout or self.default_timeout)
            return ServiceResult(True, value)
        except Exception as e:
            return ServiceResult(False, error=str(e))
            
    async def clear_cache(self, pattern: Optional[str] = None) -> ServiceResult:
        """Clear cache entries matching pattern"""
        return await self.monitor("cache_clear")(self._clear_cache)(pattern)
    
    async def _clear_cache(self, pattern: Optional[str] = None) -> ServiceResult:
        """Internal method to clear cache entries"""
        try:
            if pattern:
                # Clear specific pattern
                keys = cache.keys(pattern)
                cache.delete_many(keys)
            else:
                # Clear all cache
                cache.clear()
            return ServiceResult(True)
        except Exception as e:
            return ServiceResult(False, error=str(e))
