from typing import List, Dict, Any
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging

from source.layers.di.container import Container
from .models import Content, ContentType, ContentAsset
from source.apps.core.services import ServiceResult
from source.layers.middleware.monitoring import MetricsCollector
from source.settings.settings_manager import settings_manager

logger = logging.getLogger(__name__)
container = Container()

class BaseController:
    """Base controller with common monitoring functionality"""
    
    def __init__(self):
        self.settings = container.settings()
        self.metrics_collector = container.metrics_collector()
        
    def record_metrics(self, operation: str, result: ServiceResult):
        """Record operation metrics"""
        try:
            metrics = {
                'operation': operation,
                'success': result.success,
                'timestamp': result.timestamp.isoformat(),
                'category': 'controller'
            }
            if not result.success:
                metrics['error'] = result.error
            self.metrics_collector.record_metrics(metrics)
        except Exception as e:
            logger.error(f"Failed to record metrics for {operation}: {str(e)}")

class ContentController(BaseController):
    """Controller for handling content-related operations"""
    
    def __init__(self):
        super().__init__()
        self.content_service = container.content_creation()
        self.asset_service = container.asset_management()
        self.orchestration_service = container.content_orchestration()
        
        # Load content-specific settings
        self.content_settings = self.settings.get_category('content')
        self.validation_settings = self.settings.get_category('validation')
    
    async def create_content(self, data: Dict[str, Any], user) -> ServiceResult:
        """Create new content with enhanced pipeline"""
        try:
            # Apply validation settings
            if not self._validate_content_data(data):
                error_msg = "Content validation failed"
                logger.error(error_msg, extra={'data': data})
                return ServiceResult(False, error=error_msg)
                
            data['creator'] = user
            result = await self.content_service.create_content_with_pipeline(data)
            self.record_metrics('create_content', result)
            if result.failed:
                logger.error(f"Content creation failed: {result.error}")
                raise DRFValidationError(result.error)
            return result.data
        except ValidationError as e:
            logger.error(f"Content validation failed: {str(e)}")
            raise DRFValidationError(str(e))
            
    def _validate_content_data(self, data: Dict[str, Any]) -> bool:
        """Validate content data against settings"""
        try:
            max_title_length = self.validation_settings.get('max_title_length', 200)
            required_fields = self.validation_settings.get('required_fields', ['content_type', 'title'])
            
            if not all(field in data for field in required_fields):
                return False
                
            if len(data.get('title', '')) > max_title_length:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
            return False
    
    async def create_content_batch(self, batch_data: List[Dict[str, Any]], user) -> ServiceResult:
        """Create multiple content items in batch"""
        try:
            # Apply batch settings
            batch_size = self.content_settings.get('batch_size', 10)
            if len(batch_data) > batch_size:
                error_msg = f"Batch size exceeds maximum allowed ({batch_size})"
                logger.error(error_msg)
                return ServiceResult(False, error=error_msg)
                
            for item in batch_data:
                if not self._validate_content_data(item):
                    error_msg = "Invalid content in batch"
                    logger.error(error_msg, extra={'data': item})
                    return ServiceResult(False, error=error_msg)
                item['creator'] = user
                
            result = await self.orchestration_service.create_content_batch_with_monitoring(batch_data)
            self.record_metrics('create_content_batch', result)
            if result.failed:
                logger.error(f"Batch content creation failed: {result.error}")
                raise DRFValidationError(result.error)
            return result.data
        except ValidationError as e:
            logger.error(f"Batch content validation failed: {str(e)}")
            raise DRFValidationError(str(e))
    
    async def generate_content(self, content: Content, prompt: str) -> ServiceResult:
        """Generate content using AI"""
        try:
            result = await self.content_service.generate_content_with_ai(content, prompt)
            self.record_metrics('generate_content', result)
            if result.failed:
                logger.error(f"Content generation failed: {result.error}")
                raise DRFValidationError(result.error)
            return result.data
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise DRFValidationError(str(e))
    
    async def process_asset(self, asset: ContentAsset, file_data: Any) -> ServiceResult:
        """Process and optimize content asset"""
        try:
            result = await self.asset_service.process_asset_with_pipeline(asset)
            self.record_metrics('process_asset', result)
            if result.failed:
                logger.error(f"Asset processing failed: {result.error}")
                raise DRFValidationError(result.error)
            return result.data
        except ValidationError as e:
            logger.error(f"Asset validation failed: {str(e)}")
            raise DRFValidationError(str(e))
    
    def get_content_list(self, user, status=None):
        """Get list of content for user"""
        try:
            queryset = Content.objects.filter(creator=user, is_deleted=False)
            if status:
                queryset = queryset.filter(status=status)
            self.record_metrics('get_content_list', ServiceResult(True))
            return queryset
        except Exception as e:
            logger.error(f"Content list retrieval failed: {str(e)}")
            self.record_metrics('get_content_list', ServiceResult(False, error=str(e)))
            raise
    
    def get_content_detail(self, content_id: int, user) -> Content:
        """Get content detail"""
        try:
            content = Content.objects.get(id=content_id, creator=user, is_deleted=False)
            self.record_metrics('get_content_detail', ServiceResult(True))
            return content
        except Content.DoesNotExist as e:
            logger.error(f"Content not found: {content_id}")
            self.record_metrics('get_content_detail', ServiceResult(False, error=str(e)))
            raise
    
    async def update_content(self, content: Content, data: Dict[str, Any]) -> ServiceResult:
        """Update existing content"""
        try:
            if not self._validate_content_data(data):
                error_msg = "Invalid update data"
                logger.error(error_msg, extra={'data': data})
                return ServiceResult(False, error=error_msg)
                
            result = await self.content_service.update_content_with_pipeline(content, data)
            self.record_metrics('update_content', result)
            return result
        except ValidationError as e:
            logger.error(f"Content update failed: {str(e)}")
            self.record_metrics('update_content', ServiceResult(False, error=str(e)))
            raise DRFValidationError(str(e))
    
    async def delete_content(self, content: Content) -> ServiceResult:
        """Soft delete content"""
        try:
            result = await self.content_service.delete_content_with_cleanup(content)
            self.record_metrics('delete_content', result)
            return result
        except Exception as e:
            logger.error(f"Content deletion failed: {str(e)}")
            result = ServiceResult(False, error=str(e))
            self.record_metrics('delete_content', result)
            return result

class ContentTypeController(BaseController):
    """Controller for handling content type operations"""
    
    def __init__(self):
        super().__init__()
        self.type_settings = self.settings.get_category('content_type')
    
    def get_active_types(self):
        """Get list of active content types"""
        try:
            types = ContentType.objects.filter(is_active=True)
            self.record_metrics('get_active_types', ServiceResult(True))
            return types
        except Exception as e:
            logger.error(f"Active types retrieval failed: {str(e)}")
            self.record_metrics('get_active_types', ServiceResult(False, error=str(e)))
            raise
    
    def get_type_detail(self, type_id: int) -> ContentType:
        """Get content type detail"""
        try:
            content_type = ContentType.objects.get(id=type_id)
            self.record_metrics('get_type_detail', ServiceResult(True))
            return content_type
        except ContentType.DoesNotExist as e:
            logger.error(f"Content type not found: {type_id}")
            self.record_metrics('get_type_detail', ServiceResult(False, error=str(e)))
            raise

class AssetController(BaseController):
    """Controller for handling asset operations"""
    
    def __init__(self):
        super().__init__()
        self.asset_service = container.asset_management()
        self.asset_settings = self.settings.get_category('asset')
    
    async def upload_asset(self, content: Content, file_data: Any, asset_type: str) -> ServiceResult:
        """Upload and process new asset"""
        try:
            # Validate file size
            max_size = self.asset_settings.get('max_file_size', 100 * 1024 * 1024)  # Default 100MB
            if file_data.size > max_size:
                error_msg = f"File size exceeds maximum allowed ({max_size} bytes)"
                logger.error(error_msg)
                return ServiceResult(False, error=error_msg)
            
            result = await self.asset_service.upload_and_process_asset(content, file_data, asset_type)
            self.record_metrics('upload_asset', result)
            return result
        except Exception as e:
            logger.error(f"Asset upload failed: {str(e)}")
            result = ServiceResult(False, error=str(e))
            self.record_metrics('upload_asset', result)
            return result
    
    def get_content_assets(self, content: Content):
        """Get all assets for content"""
        try:
            assets = content.assets.all()
            self.record_metrics('get_content_assets', ServiceResult(True))
            return assets
        except Exception as e:
            logger.error(f"Asset retrieval failed: {str(e)}")
            self.record_metrics('get_content_assets', ServiceResult(False, error=str(e)))
            raise
    
    async def update_asset(self, asset: ContentAsset, data: Dict[str, Any]) -> ServiceResult:
        """Update existing asset"""
        try:
            result = await self.asset_service.update_asset_with_pipeline(asset, data)
            self.record_metrics('update_asset', result)
            return result
        except Exception as e:
            logger.error(f"Asset update failed: {str(e)}")
            result = ServiceResult(False, error=str(e))
            self.record_metrics('update_asset', result)
            return result
    
    async def delete_asset(self, asset: ContentAsset) -> ServiceResult:
        """Delete asset with cleanup"""
        try:
            result = await self.asset_service.delete_asset_with_cleanup(asset)
            self.record_metrics('delete_asset', result)
            return result
        except Exception as e:
            logger.error(f"Asset deletion failed: {str(e)}")
            result = ServiceResult(False, error=str(e))
            self.record_metrics('delete_asset', result)
            return result
