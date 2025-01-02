from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import logging

from .serializers import (
    ContentSerializer,
    ContentCreateSerializer,
    ContentBatchCreateSerializer,
    ContentTypeSerializer,
    ContentAssetSerializer
)
from .controllers import ContentController, ContentTypeController, AssetController
from .models import Content, ContentType, ContentAsset
from apps.core.permissions import IsContentCreator
from apps.core.services import ServiceResult

logger = logging.getLogger(__name__)

class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset with common functionality"""
    
    def handle_exception(self, exc):
        """Common exception handling"""
        if hasattr(self, 'controller'):
            self.controller.record_metrics(
                f"{self.action}_error",
                ServiceResult(False, error=str(exc))
            )
        return super().handle_exception(exc)

class ContentViewSet(BaseViewSet):
    """API endpoint for managing content"""
    serializer_class = ContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsContentCreator]
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ContentController()
    
    def get_queryset(self):
        status = self.request.query_params.get('status')
        return self.controller.get_content_list(self.request.user, status)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ContentCreateSerializer
        elif self.action == 'create_batch':
            return ContentBatchCreateSerializer
        return ContentSerializer
    
    async def create(self, request, *args, **kwargs):
        """Create new content"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            result = await self.controller.create_content(
                serializer.validated_data,
                request.user
            )
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            response_serializer = ContentSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Content creation failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    async def create_batch(self, request):
        """Create multiple content items"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            result = await self.controller.create_content_batch(
                serializer.validated_data['contents'],
                request.user
            )
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            response_serializer = ContentSerializer(result, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Batch content creation failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    async def update(self, request, *args, **kwargs):
        """Update existing content"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            result = await self.controller.update_content(
                instance,
                serializer.validated_data
            )
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            response_serializer = ContentSerializer(result.data)
            return Response(response_serializer.data)
        except Exception as e:
            logger.error(f"Content update failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    async def destroy(self, request, *args, **kwargs):
        """Soft delete content"""
        try:
            instance = self.get_object()
            result = await self.controller.delete_content(instance)
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Content deletion failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    async def upload_asset(self, request, pk=None):
        """Upload asset for content"""
        try:
            content = self.get_object()
            file_obj = request.FILES.get('file')
            asset_type = request.data.get('asset_type')
            
            if not file_obj or not asset_type:
                return Response(
                    {'error': 'Both file and asset_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            asset_controller = AssetController()
            result = await asset_controller.upload_asset(content, file_obj, asset_type)
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            serializer = ContentAssetSerializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Asset upload failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ContentTypeViewSet(BaseViewSet):
    """API endpoint for content types"""
    serializer_class = ContentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ContentTypeController()
    
    def get_queryset(self):
        return self.controller.get_active_types()

class ContentAssetViewSet(BaseViewSet):
    """API endpoint for managing content assets"""
    serializer_class = ContentAssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsContentCreator]
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = AssetController()
    
    def get_queryset(self):
        content_id = self.request.query_params.get('content')
        if content_id:
            content = get_object_or_404(Content, id=content_id)
            return self.controller.get_content_assets(content)
        return ContentAsset.objects.none()
    
    async def create(self, request, *args, **kwargs):
        """Create new asset"""
        try:
            content_id = request.data.get('content')
            content = get_object_or_404(Content, id=content_id)
            
            file_obj = request.FILES.get('file')
            asset_type = request.data.get('type')
            
            if not file_obj or not asset_type:
                return Response(
                    {'error': 'Both file and type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = await self.controller.upload_asset(content, file_obj, asset_type)
            
            if isinstance(result, ServiceResult) and result.failed:
                return Response(
                    {'error': result.error},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            serializer = self.get_serializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Asset creation failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
