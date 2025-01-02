from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import asyncio
import logging
from functools import wraps
import time
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and manages performance metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self._lock = threading.Lock()
        
    def record_metric(self, operation: str, duration: float, success: bool,
                     metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            self.metrics[operation].append({
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'metadata': metadata or {}
            })
            
    def get_metrics(self, operation: Optional[str] = None) -> Dict:
        with self._lock:
            if operation:
                return dict(self.metrics[operation])
            return dict(self.metrics)
            
    def clear_metrics(self):
        with self._lock:
            self.metrics.clear()

class PerformanceMonitor:
    """Monitors and tracks performance of operations"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def monitor(self, operation_name: str):
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.time() - start_time
                    self.metrics_collector.record_metric(
                        operation_name, duration, success
                    )
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.time() - start_time
                    self.metrics_collector.record_metric(
                        operation_name, duration, success
                    )
                    
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

class TelemetryMiddleware:
    """Middleware for collecting telemetry data"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        
    async def __call__(self, request, call_next):
        start_time = time.time()
        response = None
        success = True
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            success = False
            raise e
        finally:
            duration = time.time() - start_time
            self.metrics_collector.record_metric(
                f"{request.method}_{request.url.path}",
                duration,
                success,
                {
                    'status_code': getattr(response, 'status_code', None),
                    'client_ip': request.client.host,
                    'user_agent': request.headers.get('user-agent')
                }
            )

class ResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self, max_workers: int = 4):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.metrics_collector = MetricsCollector()
        
    async def execute_with_monitoring(self, func, *args, **kwargs):
        async with self.semaphore:
            start_time = time.time()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                self.metrics_collector.record_metric(
                    func.__name__,
                    duration,
                    success,
                    {'args': str(args), 'kwargs': str(kwargs)}
                )
