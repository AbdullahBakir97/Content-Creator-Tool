# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from source.layers.utils.validation import validate_api_keys
from django.utils import timezone

class User(AbstractUser):
    """Custom user model"""
    CREATOR_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    is_content_creator = models.BooleanField(default=False)
    creator_status = models.CharField(max_length=20, choices=CREATOR_STATUS_CHOICES, default='pending')
    phone_number = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return self.username

    def approve_creator_status(self):
        self.creator_status = 'approved'
        self.is_content_creator = True
        self.save()

    def reject_creator_status(self):
        self.creator_status = 'rejected'
        self.is_content_creator = False
        self.save()

    def verify_email(self):
        self.email_verified = True
        self.save()

    def update_last_login_ip(self, ip_address):
        self.last_login_ip = ip_address
        self.save()

    @property
    def is_approved_creator(self):
        return self.is_content_creator and self.creator_status == 'approved'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(blank=True)
    gemini_key = models.CharField(max_length=255, blank=True)
    eleven_labs_key = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    last_content_created = models.DateTimeField(null=True, blank=True)
    total_content_created = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'profile'
        verbose_name_plural = 'profiles'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Profile for {self.user.username}"

    def clean(self):
        # Validate API keys
        errors = validate_api_keys(self.gemini_key, self.eleven_labs_key)
        if errors:
            raise ValidationError({
                'api_keys': _('Invalid API keys: ') + ', '.join(errors)
            })

    def update_avatar(self, avatar_file):
        if self.avatar:
            self.avatar.delete(save=False)
        self.avatar = avatar_file
        self.save()

    def get_api_keys(self):
        return {
            "gemini_key": self.gemini_key,
            "eleven_labs_key": self.eleven_labs_key,
        }

    def set_social_link(self, platform, url):
        if not self.social_links:
            self.social_links = {}
        self.social_links[platform] = url
        self.save()

    def set_preference(self, key, value):
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
        self.save()

    def increment_content_count(self):
        self.total_content_created += 1
        self.last_content_created = timezone.now()
        self.save()