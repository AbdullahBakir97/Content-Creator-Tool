from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Content, ContentType, ContentAsset
from .controllers import ContentController, ContentTypeController, AssetController
from source.layers.di.container import Container

container = Container()

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'creator', 'status', 'duration', 'scheduled_time', 'created_at', 'updated_at')
    list_filter = ('content_type', 'status', 'creator', 'created_at')
    search_fields = ('title', 'script', 'creator__username')
    readonly_fields = (
        'created_at', 'updated_at', 'processing_started_at', 
        'processing_completed_at', 'error_message'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content_type', 'creator', 'status')
        }),
        ('Content Details', {
            'fields': ('script', 'duration', 'scheduled_time')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail')
        }),
        ('Processing Information', {
            'fields': ('processing_started_at', 'processing_completed_at', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    change_list_template = 'admin/content/change_list.html'
    change_form_template = 'admin/content/content/change_form.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_controller = ContentController()
        self.type_controller = ContentTypeController()
        self.asset_controller = AssetController()
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('save/', self.admin_site.admin_view(self.save_content), name='content_content_save'),
            path('generate/', self.admin_site.admin_view(self.generate_content), name='content_content_generate'),
            path('assets/', self.admin_site.admin_view(self.manage_assets), name='content_content_assets'),
            path('upload-asset/', self.admin_site.admin_view(self.upload_asset), name='content_content_upload_asset'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'content_types': self.type_controller.get_active_types(),
            'content_stats': self._get_content_stats(request.user)
        })
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            content = get_object_or_404(Content, id=object_id)
            extra_context.update({
                'content_types': self.type_controller.get_active_types(),
                'content_assets': self.asset_controller.get_content_assets(content),
                'asset_analytics': self._get_asset_analytics(content)
            })
        return super().change_view(request, object_id, form_url, extra_context)
    
    def _get_content_stats(self, user):
        """Get content statistics for dashboard"""
        total = Content.objects.filter(creator=user).count()
        in_progress = Content.objects.filter(creator=user, status='in_progress').count()
        completed = Content.objects.filter(creator=user, status='completed').count()
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'in_progress': in_progress,
            'completed': completed,
            'success_rate': round(success_rate, 1)
        }
    
    def _get_asset_analytics(self, content):
        """Get analytics data for content assets"""
        assets = content.assets.all()
        return {
            'total': assets.count(),
            'by_type': {
                'image': assets.filter(type='image').count(),
                'video': assets.filter(type='video').count(),
                'audio': assets.filter(type='audio').count()
            }
        }
    
    @require_http_methods(["POST"])
    def save_content(self, request):
        """Save content with enhanced validation"""
        try:
            data = request.POST.dict()
            if 'id' in data:
                content = get_object_or_404(Content, id=data['id'])
                result = self.content_controller.update_content(content, data)
            else:
                result = self.content_controller.create_content(data, request.user)
            
            if result.success:
                return JsonResponse({
                    'success': True,
                    'message': 'Content saved successfully',
                    'redirect': reverse('admin:content_content_changelist')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.error
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @api_view(['POST'])
    def generate_content(self, request):
        """Generate content using AI"""
        try:
            content_id = request.data.get('content_id')
            prompt = request.data.get('prompt')
            
            if not content_id or not prompt:
                return Response({
                    'success': False,
                    'error': 'Missing required parameters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            content = get_object_or_404(Content, id=content_id)
            result = self.content_controller.generate_content(content, prompt)
            
            return Response({
                'success': True,
                'data': result.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @api_view(['GET', 'POST', 'DELETE'])
    def manage_assets(self, request):
        """Manage content assets"""
        try:
            content_id = request.GET.get('content_id') or request.data.get('content_id')
            content = get_object_or_404(Content, id=content_id)
            
            if request.method == 'GET':
                assets = self.asset_controller.get_content_assets(content)
                return Response({
                    'success': True,
                    'data': assets
                })
            elif request.method == 'POST':
                asset_id = request.data.get('asset_id')
                asset_data = request.data.get('asset_data')
                
                if asset_id:
                    # Update existing asset
                    asset = get_object_or_404(ContentAsset, id=asset_id)
                    result = self.asset_controller.update_asset(asset, asset_data)
                else:
                    # Create new asset
                    result = self.asset_controller.create_asset(content, asset_data)
                
                return Response({
                    'success': True,
                    'data': result.data
                })
            elif request.method == 'DELETE':
                asset_id = request.data.get('asset_id')
                asset = get_object_or_404(ContentAsset, id=asset_id)
                result = self.asset_controller.delete_asset(asset)
                
                return Response({
                    'success': True,
                    'message': 'Asset deleted successfully'
                })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @api_view(['POST'])
    def upload_asset(self, request):
        """Upload and process new asset"""
        try:
            content_id = request.data.get('content_id')
            file_data = request.FILES.get('file')
            asset_type = request.data.get('type')
            
            if not all([content_id, file_data, asset_type]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            content = get_object_or_404(Content, id=content_id)
            result = self.asset_controller.upload_asset(content, file_data, asset_type)
            
            return Response({
                'success': True,
                'data': result.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = ContentTypeController()

@admin.register(ContentAsset)
class ContentAssetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'content', 'asset_type', 'order', 'created_at')
    list_filter = ('asset_type', 'created_at')
    search_fields = ('content__title', 'asset_type')
    readonly_fields = ('created_at', 'updated_at')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = AssetController()

# Register custom admin site header and title
admin.site.site_header = 'Content Creator Tool Administration'
admin.site.site_title = 'Content Creator Tool Admin'
admin.site.index_title = 'Content Management Dashboard'
