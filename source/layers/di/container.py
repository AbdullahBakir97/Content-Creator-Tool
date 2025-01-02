from dependency_injector import containers, providers
from django.conf import settings

from source.apps.content.enhanced_services import (
    EnhancedContentCreationService,
    EnhancedAssetManagementService,
    EnhancedContentOrchestrationService,
)
from source.apps.core.cache_manager import CacheManager
from source.layers.middleware.monitoring import (
    PerformanceMonitor,
    ResourceMonitor,
    MetricsCollector
)
from source.layers.ai.content_generation import ContentGenerationUtility
from source.layers.ai.voiceover_generation import VoiceoverGenerationUtility
from source.settings.settings_manager import settings_manager

class Container(containers.DeclarativeContainer):
    """Dependency Injection Container"""
    
    # Settings Manager
    settings = providers.Object(settings_manager)
    
    # Settings Categories
    monitoring_settings = providers.Callable(
        lambda: settings_manager.get_monitoring_settings()
    )
    
    resource_limits = providers.Callable(
        lambda: settings_manager.get_resource_limits()
    )
    
    ai_settings = providers.Callable(
        lambda: settings_manager.get_category('ai')
    )
    
    # Core Services
    metrics_collector = providers.Singleton(MetricsCollector)
    
    performance_monitor = providers.Singleton(
        PerformanceMonitor
    )
    
    resource_monitor = providers.Singleton(
        ResourceMonitor,
        max_workers=providers.Callable(
            lambda: settings_manager.get_resource_limits().get('max_workers', 4)
        )
    )
    
    cache_manager = providers.Singleton(
        CacheManager,
        settings=settings,
        performance_monitor=performance_monitor
    )
    
    # AI Services
    content_generation = providers.Singleton(
        ContentGenerationUtility,
        gemini_key=providers.Callable(
            lambda: settings_manager.get_category('ai').get('gemini_key')
        )
    )
    
    voiceover_generation = providers.Singleton(
        VoiceoverGenerationUtility,
        api_key=providers.Callable(
            lambda: settings_manager.get_category('ai').get('eleven_labs_key')
        )
    )
    
    # Enhanced Services
    content_creation = providers.Singleton(
        EnhancedContentCreationService,
        content_generation=content_generation,
        voiceover_generation=voiceover_generation,
        performance_monitor=performance_monitor,
        resource_monitor=resource_monitor,
        settings=settings
    )
    
    asset_management = providers.Singleton(
        EnhancedAssetManagementService,
        performance_monitor=performance_monitor,
        resource_monitor=resource_monitor,
        settings=settings
    )
    
    content_orchestration = providers.Singleton(
        EnhancedContentOrchestrationService,
        performance_monitor=performance_monitor,
        gemini_key=providers.Callable(
            lambda: settings_manager.get_category('ai').get('gemini_key')
        ),
        eleven_labs_key=providers.Callable(
            lambda: settings_manager.get_category('ai').get('eleven_labs_key')
        ),
        settings=settings
    )
