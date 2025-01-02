# apps/content/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class ContentType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    prompt_template = models.TextField(help_text="Template for AI content generation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'content type'
        verbose_name_plural = 'content types'

    def __str__(self):
        return self.name

class Content(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
    )

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    script = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    video_file = models.FileField(upload_to='content/videos/', blank=True)
    thumbnail = models.ImageField(upload_to='content/thumbnails/', blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=60, help_text="Duration in seconds")
    error_message = models.TextField(blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'content'
        verbose_name_plural = 'contents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def set_status(self, new_status, error_message=None):
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
            
        self.status = new_status
        if new_status == 'processing':
            self.processing_started_at = timezone.now()
        elif new_status in ['completed', 'failed']:
            self.processing_completed_at = timezone.now()
        
        if error_message:
            self.error_message = error_message
            
        self.save()

    def schedule_content(self, scheduled_time):
        if scheduled_time <= timezone.now():
            raise ValueError("Scheduled time must be in the future")
        self.scheduled_time = scheduled_time
        self.set_status('scheduled')

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def get_processing_duration(self):
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

    @property
    def is_ready_for_processing(self):
        return self.status == 'draft' and not self.is_deleted

    @property
    def is_scheduled_for_now(self):
        if self.status == 'scheduled' and self.scheduled_time:
            return self.scheduled_time <= timezone.now()
        return False

class ContentAsset(models.Model):
    ASSET_TYPES = (
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('subtitle', 'Subtitle'),
        ('other', 'Other'),
    )

    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='assets')
    file = models.FileField(upload_to='content/assets/')
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPES)
    order = models.IntegerField(default=0)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds for audio/video assets")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'content asset'
        verbose_name_plural = 'content assets'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.get_asset_type_display()} for {self.content.title}"

    def upload_asset(self, file):
        self.file = file
        self.save()

    def set_metadata(self, key, value):
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value
        self.save()
