from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import ContentViewSet, ContentTypeViewSet, ContentAssetViewSet
from . import api

# Main router for top-level endpoints
router = DefaultRouter()
router.register(r'content', api.ContentViewSet, basename='content')
router.register(r'content-types', api.ContentTypeViewSet, basename='content-type')

# Nested router for content assets
content_router = routers.NestedDefaultRouter(router, r'content', lookup='content')
content_router.register(r'assets', ContentAssetViewSet, basename='content-asset')

urlpatterns = [
    # API Schema and documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(content_router.urls)),
    
    # Admin custom views (these are registered in admin.py)
    path('admin/content/save/', views.save_content, name='admin_content_save'),
    path('admin/content/generate/', views.generate_content, name='admin_content_generate'),
    path('admin/content/assets/', views.manage_assets, name='admin_content_assets'),
    path('admin/content/upload-asset/', views.upload_asset, name='admin_content_upload_asset'),
]
