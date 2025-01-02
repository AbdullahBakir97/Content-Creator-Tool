from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
import magic
import logging

from .services import (
    ContentCreationService,
    ContentService,
    ContentTypeService,
    AssetManagementService,
    ContentOrchestrationService
)
from .models import Content, ContentType, ContentAsset
from source.layers.middleware.monitoring import (
    PerformanceMonitor,
    ResourceMonitor,
    MetricsCollector
)
from source.apps.core.services import ServiceResult
from source.layers.ai.content_generation import ContentGenerationUtility
from source.layers.ai.voiceover_generation import VoiceoverGenerationUtility
from source.settings.settings_manager import settings_manager

logger = logging.getLogger(__name__)

class EnhancedContentCreationService(ContentCreationService):
    """Enhanced content creation service with monitoring and advanced features"""
    
    def __init__(self, content_generation: ContentGenerationUtility,
                 voiceover_generation: VoiceoverGenerationUtility,
                 performance_monitor: PerformanceMonitor,
                 resource_monitor: ResourceMonitor,
                 settings=None,
                 **kwargs):
        super().__init__(
            content_generation=content_generation,
            voiceover_generation=voiceover_generation,
            settings=settings or settings_manager,
            **kwargs
        )
        self.performance_monitor = performance_monitor
        self.resource_monitor = resource_monitor
        self.metrics_collector = MetricsCollector()
        
    @property
    def monitor(self):
        """Get performance monitor decorator"""
        return self.performance_monitor.monitor
        
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate input data for content creation"""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
            
        required_fields = ['request', 'content_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
            
        request = data.get('request', {})
        if not isinstance(request, dict):
            raise ValidationError("Request must be a dictionary")
            
        if 'content_type' not in request:
            raise ValidationError("Content type is required in request")
        
    async def create_content_with_pipeline(self, request: Dict[str, Any]) -> ServiceResult:
        """Create content using an enhanced pipeline with monitoring"""
        # Get content settings
        content_settings = self.settings.get_category('content')
        max_retries = content_settings['max_retries']
        timeout = content_settings['processing_timeout']
        
        # Validate request
        if not self._validate_content_request(request):
            return ServiceResult(False, error="Invalid request")
            
        # Execute pipeline with monitoring
        return await self.monitor("create_content_pipeline")(self._execute_pipeline)(request, max_retries, timeout)
    
    async def _execute_pipeline(self, request: Dict[str, Any], max_retries: int, timeout: int) -> ServiceResult:
        """Execute the content creation pipeline"""
        context = {'request': request}
        
        # Generate script
        script_result = await self.resource_monitor.execute_with_monitoring(
            self._generate_script,
            context,
            timeout=timeout,
            max_retries=max_retries
        )
        if script_result.failed:
            return script_result
        context.update(script_result.data)
        
        # Generate voiceover
        voiceover_result = await self.resource_monitor.execute_with_monitoring(
            self._generate_voiceover,
            context,
            timeout=timeout,
            max_retries=max_retries
        )
        if voiceover_result.failed:
            return voiceover_result
        context.update(voiceover_result.data)
        
        # Process assets
        assets_result = await self.resource_monitor.execute_with_monitoring(
            self._process_assets,
            context,
            timeout=timeout,
            max_retries=max_retries
        )
        if assets_result.failed:
            return assets_result
        context.update(assets_result.data)
            
        return ServiceResult(True, context)
        
    def _validate_content_request(self, request: Dict[str, Any]) -> bool:
        """Validate the content creation request"""
        required_fields = ['content_type', 'title']
        return all(field in request for field in required_fields)

class EnhancedAssetManagementService(AssetManagementService):
    """Enhanced asset management service with processing pipeline"""
    
    def __init__(self, performance_monitor: PerformanceMonitor,
                 resource_monitor: ResourceMonitor,
                 settings=None,
                 **kwargs):
        super().__init__(settings=settings or settings_manager, **kwargs)
        self.performance_monitor = performance_monitor
        self.resource_monitor = resource_monitor
        self.metrics_collector = MetricsCollector()
        
    @property
    def monitor(self):
        """Get performance monitor decorator"""
        return self.performance_monitor.monitor
        
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate asset data"""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
            
        if 'file' not in data:
            raise ValidationError("File data is required")
            
        if 'asset_type' not in data:
            raise ValidationError("Asset type is required")
            
        if 'content' not in data:
            raise ValidationError("Content reference is required")
            
        if not isinstance(data['content'], Content):
            raise ValidationError("Invalid content reference")
        
    async def process_asset_with_pipeline(self, asset: ContentAsset) -> ServiceResult:
        """Process asset using type-specific pipeline with monitoring"""
        return await self.monitor("asset_processing")(self._process_asset_pipeline)(asset)
    
    async def _process_asset_pipeline(self, asset: ContentAsset) -> ServiceResult:
        """Internal method to process asset with pipeline"""
        try:
            # Upload asset using base service method
            upload_result = await super().upload_asset(
                asset.content,
                asset.file,
                asset.asset_type
            )
            if upload_result.failed:
                return upload_result
                
            # Process based on asset type
            if asset.asset_type == 'image':
                await self._process_image(asset)
            elif asset.asset_type == 'audio':
                await self._process_audio(asset)
            elif asset.asset_type == 'video':
                await self._process_video(asset)
                
            return ServiceResult(True, asset)
        except Exception as e:
            logger.error(f"Asset processing failed: {str(e)}")
            return ServiceResult(False, error=str(e))
            
    async def _process_image(self, asset: ContentAsset) -> None:
        """Process image asset with monitoring"""
        asset_settings = self.settings.get_category('asset')
        max_dimension = asset_settings['image_max_dimension']
        # Basic image processing using settings
        # Actual implementation would depend on image processing library
        pass
        
    async def _process_audio(self, asset: ContentAsset) -> None:
        """Process audio asset with monitoring"""
        asset_settings = self.settings.get_category('asset')
        max_duration = asset_settings['audio_max_duration']
        # Basic audio processing using settings
        # Actual implementation would depend on audio processing library
        pass
        
    async def _process_video(self, asset: ContentAsset) -> None:
        """Process video asset with monitoring"""
        asset_settings = self.settings.get_category('asset')
        video_settings = self.settings.get_category('video')
        max_duration = asset_settings['video_max_duration']
        resolution = video_settings['default_resolution']
        framerate = video_settings['default_framerate']
        bitrate = video_settings['default_bitrate']
        # Basic video processing using settings
        # Actual implementation would depend on video processing library
        pass

class EnhancedContentOrchestrationService(ContentOrchestrationService):
    """Enhanced content orchestration service with batch processing and monitoring"""
    
    def __init__(self, performance_monitor: PerformanceMonitor,
                 gemini_key: str, eleven_labs_key: str,
                 settings=None,
                 **kwargs):
        super().__init__(
            gemini_key=gemini_key,
            eleven_labs_key=eleven_labs_key,
            settings=settings or settings_manager,
            **kwargs
        )
        self.performance_monitor = performance_monitor
        self.metrics_collector = MetricsCollector()
        
    @property
    def monitor(self):
        """Get performance monitor decorator"""
        return self.performance_monitor.monitor
        
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate batch configuration data"""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
            
        if 'batch_config' not in data:
            raise ValidationError("Batch configuration is required")
            
        if not isinstance(data['batch_config'], list):
            raise ValidationError("Batch configuration must be a list")
            
        for idx, config in enumerate(data['batch_config']):
            if not isinstance(config, dict):
                raise ValidationError(f"Configuration at index {idx} must be a dictionary")
                
            required_fields = ['content_type', 'title']
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise ValidationError(f"Missing required fields in config {idx}: {', '.join(missing_fields)}")
        
    async def create_content_batch_with_monitoring(
        self, batch_config: List[Dict]
    ) -> ServiceResult:
        """Create multiple content items with monitoring"""
        return await self.monitor("batch_creation")(self._create_batch_with_monitoring)(batch_config)
    
    async def _create_batch_with_monitoring(
        self, batch_config: List[Dict]
    ) -> ServiceResult:
        """Internal method to create batch with monitoring"""
        async with self._batch_monitor() as monitor:
            # Use base service's batch creation with monitoring
            result = await super().create_content_batch(batch_config)
            
            if isinstance(result, ServiceResult):
                monitor.record_metrics({
                    'total': len(batch_config),
                    'successful': len(result.data) if result.success else 0,
                    'failed': len(batch_config) - len(result.data) if result.success else len(batch_config)
                })
                
                if result.success:
                    result.data['metrics'] = monitor.get_metrics()
                
            return result
            
    async def _batch_monitor(self):
        """Context manager for batch operation monitoring"""
        class BatchMonitor:
            def __init__(self):
                self.start_time = None
                self.metrics = {}
                
            async def __aenter__(self):
                self.start_time = datetime.now()
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                duration = (datetime.now() - self.start_time).total_seconds()
                self.metrics['duration'] = duration
                
            def record_metrics(self, metrics: Dict):
                self.metrics.update(metrics)
                
            def get_metrics(self) -> Dict:
                return self.metrics
                
        return BatchMonitor()
