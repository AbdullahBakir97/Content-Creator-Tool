# apps/core/models.py
from django.db import models
from django.core.cache import cache
from django.conf import settings

class Setting(models.Model):
    SETTING_TYPES = (
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    )

    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    category = models.CharField(max_length=50, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'setting'
        verbose_name_plural = 'settings'
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.key} ({self.get_value_type_display()})"

    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value with caching"""
        cache_key = f'setting_{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(key=key)
                value = setting.get_typed_value()
                cache.set(cache_key, value, timeout=3600)  # Cache for 1 hour
            except cls.DoesNotExist:
                return default
                
        return value

    @classmethod
    def update_setting(cls, key, value, value_type='string', description=None):
        """Update or create setting with proper type conversion"""
        setting, created = cls.objects.get_or_create(key=key)
        setting.value = str(value)
        setting.value_type = value_type
        
        if description:
            setting.description = description
            
        setting.save()
        cache.delete(f'setting_{key}')
        return setting

    def get_typed_value(self):
        """Convert stored string value to proper type"""
        import json
        
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() == 'true'
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value  # Default to string

    @classmethod
    def get_category_settings(cls, category):
        """Get all settings for a specific category"""
        return cls.objects.filter(category=category)

    @classmethod
    def get_public_settings(cls):
        """Get all public settings"""
        return cls.objects.filter(is_public=True)

    @classmethod
    def bulk_update_settings(cls, settings_dict):
        """Bulk update multiple settings at once"""
        for key, value in settings_dict.items():
            cls.update_setting(key, value)
            
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(f'setting_{self.key}')
