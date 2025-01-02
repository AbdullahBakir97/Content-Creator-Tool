from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
import asyncio
import logging
from io import BytesIO
import magic

from .models import Content, ContentType, ContentAsset
from source.apps.core.services import BaseService, ServiceResult
from source.layers.ai.content_generation import ContentGenerationUtility
from source.layers.ai.voiceover_generation import VoiceoverGenerationUtility
from source.settings.settings_manager import settings_manager

logger = logging.getLogger(__name__)

class ContentCreationService(BaseService):
    """Service for content creation with AI integration"""

    def __init__(self, content_generation: ContentGenerationUtility,
                 voiceover_generation: VoiceoverGenerationUtility, **kwargs):
        super().__init__()
        self.content_gen = content_generation
        self.voiceover_gen = voiceover_generation
        self.settings = kwargs.get('settings', settings_manager)

    async def _generate_script(self, context: Dict) -> ServiceResult:
        """Generate content script using AI"""
        try:
            content_type = context['request'].get('content_type')
            ai_settings = self.settings.get_category('ai')
            
            script_result = await self.content_gen.generate_script(
                content_type,
                max_retries=ai_settings['max_retries'],
                timeout=ai_settings['timeout']
            )
            if script_result.failed:
                return script_result

            return ServiceResult(True, {
                'script': script_result.data['script'],
                'script_metrics': script_result.data['metrics']
            })
        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    async def _generate_voiceover(self, context: Dict) -> ServiceResult:
        """Generate voiceover from script"""
        try:
            script = context.get('script')
            if not script:
                return ServiceResult(False, error="Script not found in context")

            ai_settings = self.settings.get_category('ai')
            voiceover_result = await self.voiceover_gen.generate_voiceover(
                script,
                max_retries=ai_settings['max_retries'],
                timeout=ai_settings['timeout']
            )
            
            if voiceover_result.failed:
                return voiceover_result

            return ServiceResult(True, {
                'voiceover': voiceover_result.data['audio'],
                'voiceover_metrics': voiceover_result.data['metrics']
            })
        except Exception as e:
            logger.error(f"Voiceover generation failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    async def _process_assets(self, context: Dict) -> ServiceResult:
        """Process content assets"""
        try:
            asset_settings = self.settings.get_category('asset')
            content = context.get('content')
            if not content:
                return ServiceResult(False, error="Content not found in context")

            processed_assets = []
            for asset in content.assets.all():
                if not self._validate_asset(asset, asset_settings):
                    continue

                processed_result = await self._process_single_asset(
                    asset, asset_settings
                )
                if processed_result.success:
                    processed_assets.append(processed_result.data)

            return ServiceResult(True, {'processed_assets': processed_assets})
        except Exception as e:
            logger.error(f"Asset processing failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    def _validate_asset(self, asset: ContentAsset, settings: Dict) -> bool:
        """Validate asset against settings"""
        try:
            file_size = asset.file.size if asset.file else 0
            if file_size > settings['max_file_size']:
                logger.warning(f"Asset {asset.id} exceeds max file size")
                return False

            mime_type = magic.from_buffer(asset.file.read(1024), mime=True)
            asset.file.seek(0)

            type_mapping = {
                'image': 'allowed_image_types',
                'audio': 'allowed_audio_types',
                'video': 'allowed_video_types'
            }
            allowed_types = settings.get(type_mapping.get(asset.asset_type, []))
            if mime_type not in allowed_types:
                logger.warning(f"Asset {asset.id} has invalid mime type: {mime_type}")
                return False

            return True
        except Exception as e:
            logger.error(f"Asset validation failed: {str(e)}")
            return False

    async def _process_single_asset(self, asset: ContentAsset, 
                                  settings: Dict) -> ServiceResult:
        """Process a single asset"""
        try:
            # Process based on asset type
            if asset.asset_type == 'image':
                return await self._process_image(asset, settings)
            elif asset.asset_type == 'video':
                return await self._process_video(asset, settings)
            elif asset.asset_type == 'audio':
                return await self._process_audio(asset, settings)
            else:
                return ServiceResult(False, error=f"Unsupported asset type: {asset.asset_type}")
        except Exception as e:
            logger.error(f"Asset processing failed: {str(e)}")
            return ServiceResult(False, error=str(e))

class ContentService(BaseService):
    """Service for basic content operations"""

    def __init__(self, **kwargs):
        super().__init__()
        self.settings = kwargs.get('settings', settings_manager)

    async def create_content(self, creator: Any, content_type: str,
                           title: str, script: str) -> ServiceResult:
        """Create content entry with validation"""
        try:
            # Validate against settings
            content_settings = self.settings.get_category('content')
            if len(script) > content_settings.get('max_script_length', 10000):
                return ServiceResult(False, error="Script exceeds maximum length")

            content = Content.objects.create(
                creator=creator,
                content_type=content_type,
                title=title,
                script=script
            )
            return ServiceResult(True, content)
        except Exception as e:
            logger.error(f"Content creation failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    async def update_content(self, content: Content, **data) -> ServiceResult:
        """Update content with validation"""
        try:
            content_settings = self.settings.get_category('content')
            if 'script' in data and len(data['script']) > content_settings.get('max_script_length', 10000):
                return ServiceResult(False, error="Script exceeds maximum length")

            for key, value in data.items():
                setattr(content, key, value)
            content.save()
            return ServiceResult(True, content)
        except Exception as e:
            logger.error(f"Content update failed: {str(e)}")
            return ServiceResult(False, error=str(e))

class ContentTypeService(BaseService):
    """Service for content type operations"""

    def __init__(self, **kwargs):
        super().__init__()
        self.settings = kwargs.get('settings', settings_manager)

    async def get_active_content_types(self) -> ServiceResult[List[ContentType]]:
        """Get active content types"""
        try:
            types = ContentType.objects.filter(is_active=True)
            return ServiceResult(True, list(types))
        except Exception as e:
            logger.error(f"Failed to get content types: {str(e)}")
            return ServiceResult(False, error=str(e))

class AssetManagementService(BaseService):
    """Service for asset management"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.settings = kwargs.get('settings', settings_manager)
        
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate asset data"""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
            
        if 'file' not in data:
            raise ValidationError("File data is required")
            
        if 'asset_type' not in data:
            raise ValidationError("Asset type is required")
            
        if data['asset_type'] not in ['image', 'audio', 'video']:
            raise ValidationError("Invalid asset type. Must be one of: image, audio, video")
            
        if 'content' not in data:
            raise ValidationError("Content reference is required")
            
        if not isinstance(data['content'], Content):
            raise ValidationError("Invalid content reference")
            
        if 'metadata' in data and not isinstance(data['metadata'], dict):
            raise ValidationError("Metadata must be a dictionary")
        
    async def upload_asset(self, content: Content, file_data: BinaryIO,
                         asset_type: str) -> ServiceResult:
        """Upload and validate asset"""
        try:
            self._validate({
                'file': file_data,
                'asset_type': asset_type,
                'content': content
            })
            
            mime = magic.from_buffer(file_data.read(), mime=True)
            file_data.seek(0)  # Reset file pointer
            
            # Validate mime type matches asset_type
            valid_mimes = {
                'image': ['image/jpeg', 'image/png', 'image/gif'],
                'audio': ['audio/mpeg', 'audio/wav', 'audio/ogg'],
                'video': ['video/mp4', 'video/quicktime', 'video/x-msvideo']
            }
            
            if mime not in valid_mimes.get(asset_type, []):
                return ServiceResult(False, error=f"Invalid file type for {asset_type}: {mime}")
            
            asset = ContentAsset.objects.create(
                content=content,
                asset_type=asset_type,
                file=file_data,
                mime_type=mime
            )
            
            return ServiceResult(True, {'asset': asset})
            
        except ValidationError as e:
            logger.error(f"Asset validation failed: {str(e)}")
            return ServiceResult(False, error=str(e))
        except Exception as e:
            logger.error(f"Asset upload failed: {str(e)}")
            return ServiceResult(False, error=str(e))

class ContentManagementService(BaseService):
    """Service for content management"""

    def __init__(self, **kwargs):
        super().__init__()
        self.settings = kwargs.get('settings', settings_manager)

    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate content data for management operations"""
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
            
        if 'content_type' not in data:
            raise ValidationError("Content type is required")
            
        if 'title' not in data:
            raise ValidationError("Title is required")
            
        if 'script' in data and not isinstance(data['script'], str):
            raise ValidationError("Script must be a string")
            
        if 'status' in data and data['status'] not in ['draft', 'published', 'archived']:
            raise ValidationError("Invalid content status")
            
        if 'metadata' in data and not isinstance(data['metadata'], dict):
            raise ValidationError("Metadata must be a dictionary")

    async def process_batch_content(self, content_list: List[Dict[str, Any]]) -> ServiceResult:
        """Process multiple content items in batch"""
        try:
            results = []
            for content_data in content_list:
                result = await self._process_single_content(content_data)
                results.append(result)
            return ServiceResult(True, {'results': results})
        except Exception as e:
            logger.error(f"Batch content processing failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    async def _process_single_content(self, content_data: Dict[str, Any]) -> ServiceResult:
        """Process single content item"""
        try:
            self._validate(content_data)
            
            content_type = content_data['content_type']
            title = content_data['title']
            script = content_data.get('script', '')
            status = content_data.get('status', 'draft')
            metadata = content_data.get('metadata', {})
            
            content = Content.objects.create(
                content_type=content_type,
                title=title,
                script=script,
                status=status,
                metadata=metadata
            )
            
            return ServiceResult(True, {'content': content})
        except ValidationError as e:
            logger.error(f"Content validation failed: {str(e)}")
            return ServiceResult(False, error=str(e))
        except Exception as e:
            logger.error(f"Content processing failed: {str(e)}")
            return ServiceResult(False, error=str(e))

class ContentOrchestrationService(BaseService):
    """Service for content orchestration"""

    def __init__(self, gemini_key: str, eleven_labs_key: str, **kwargs):
        super().__init__()
        self.content_gen = ContentGenerationUtility(gemini_key)
        self.voiceover_gen = VoiceoverGenerationUtility(eleven_labs_key)
        self.settings = kwargs.get('settings', settings_manager)
        self.content_mgmt = ContentManagementService()
        self.asset_mgmt = AssetManagementService()

    async def create_content_batch(self, batch_config: List[Dict[str, Any]]) -> ServiceResult[List[Dict[str, Any]]]:
        """Create multiple content items in parallel with optimizations"""
        try:
            # Generate scripts in parallel
            script_results = await self.content_gen.batch_generate_scripts(batch_config)
            if script_results.failed:
                return script_results

            # Generate voiceovers in parallel
            voiceover_configs = [
                {'text': result['script']} for result in script_results.data
                if result is not None
            ]
            voiceover_results = await self.voiceover_gen.batch_generate_voiceovers(voiceover_configs)
            if voiceover_results.failed:
                return voiceover_results

            # Create content items
            content_items = []
            for i, config in enumerate(batch_config):
                if script_results.data[i] and voiceover_results.data[i]:
                    content_item = {
                        'title': config['title'],
                        'content_type': config['content_type'],
                        'script': script_results.data[i]['script'],
                        'script_metrics': script_results.data[i]['metrics'],
                        'voiceover': voiceover_results.data[i]['audio'],
                        'voiceover_metrics': voiceover_results.data[i]['metrics']
                    }
                    content_items.append(content_item)

            # Process content items
            results = await self.content_mgmt.process_batch_content(content_items)

            logger.info(
                f"Batch content creation completed",
                extra={
                    'total_items': len(batch_config),
                    'successful_items': len(content_items)
                }
            )

            return results
        except Exception as e:
            logger.error(f"Batch content creation failed: {str(e)}")
            return ServiceResult(False, error=str(e))

    async def optimize_content(self, content_id: int,
                             optimization_config: Dict[str, Any]) -> ServiceResult[Content]:
        """Optimize existing content"""
        try:
            content = Content.objects.get(id=content_id)

            # Optimize script if needed
            if 'script_metrics' in optimization_config:
                script_result = await self.content_gen.optimize_script(
                    content.script,
                    optimization_config['script_metrics']
                )
                if script_result.success:
                    content.script = script_result.data['script']
                    content.script_metrics = script_result.data['metrics']

            # Optimize voiceover if needed
            if 'voiceover_metrics' in optimization_config:
                voiceover_result = await self.voiceover_gen.optimize_voice_settings(
                    content.script,
                    optimization_config['voiceover_metrics']
                )
                if voiceover_result.success:
                    self.asset_mgmt.save_file(
                        voiceover_result.data['audio'],
                        content.voiceover_path
                    )
                    content.voiceover_metrics = voiceover_result.data['metrics']

            content.save()

            logger.info(
                f"Content optimized successfully: {content.id}",
                extra={
                    'content_id': content.id,
                    'optimization_config': optimization_config
                }
            )

            return ServiceResult(True, content)
        except Content.DoesNotExist:
            return ServiceResult(False, error=f"Content not found: {content_id}")
        except Exception as e:
            logger.error(f"Content optimization failed: {str(e)}")
            return ServiceResult(False, error=str(e))