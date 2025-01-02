from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
from typing import Optional, Dict, Any
from .models import User, Profile
from apps.core.services import BaseService, ServiceResult
from apps.core.services import LoggingService
import jwt
from datetime import datetime, timedelta
from django.conf import settings

class UserService(BaseService):
    """Enhanced user management service"""

    def _validate(self, data: Dict[str, Any]) -> None:
        if 'username' not in data:
            raise ValidationError("Username is required")
        if 'password' not in data and not data.get('is_social_auth'):
            raise ValidationError("Password is required for non-social auth")

    def register_user(self, username: str, password: str, 
                     **extra_fields) -> ServiceResult[User]:
        """Register new user with validation"""
        try:
            validation_result = self.validate({
                'username': username,
                'password': password,
                **extra_fields
            })
            if validation_result.failed:
                return ServiceResult(False, None, validation_result.error)

            with transaction.atomic():
                user = User(username=username, **extra_fields)
                user.set_password(password)
                user.save()

                # Create profile
                Profile.objects.create(user=user)

                LoggingService.log_info(
                    f"User registered successfully: {username}",
                    extra={'user_id': user.id}
                )
                return ServiceResult(True, user)

        except Exception as e:
            self.add_error(str(e), 'registration_error')
            return ServiceResult(False, None, str(e))

    def authenticate_user(self, username: str, 
                         password: str) -> ServiceResult[Dict[str, Any]]:
        """Authenticate user and generate token"""
        try:
            user = authenticate(username=username, password=password)
            if not user:
                return ServiceResult(
                    False, None, 
                    "Invalid credentials",
                    {'auth_failed': True}
                )

            # Generate JWT token
            token = self._generate_token(user)
            
            LoggingService.log_info(
                f"User authenticated: {username}",
                extra={'user_id': user.id}
            )
            
            return ServiceResult(True, {
                'user': user,
                'token': token,
                'profile': user.profile
            })

        except Exception as e:
            self.add_error(str(e), 'authentication_error')
            return ServiceResult(False, None, str(e))

    def _generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def get_user_profile(self, user: User) -> ServiceResult[Profile]:
        """Get user profile with caching"""
        try:
            cache_key = f"profile:{user.id}"
            profile = self.get_cached(cache_key)
            
            if not profile:
                profile = user.profile
                self.set_cached(cache_key, profile)
                
            return ServiceResult(True, profile)
        except Exception as e:
            self.add_error(str(e), 'profile_error')
            return ServiceResult(False, None, str(e))

    def update_user_profile(self, user: User, 
                          **profile_data) -> ServiceResult[Profile]:
        """Update user profile with validation"""
        try:
            with transaction.atomic():
                profile = user.profile
                
                # Validate profile data
                if not self._validate_profile_data(profile_data):
                    return ServiceResult(
                        False, None, 
                        "Invalid profile data",
                        {'validation_errors': self.get_errors()}
                    )
                
                # Update profile
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()
                
                # Clear cache
                self.clear_cached(f"profile:{user.id}")
                
                LoggingService.log_info(
                    f"Profile updated for user: {user.username}",
                    extra={'user_id': user.id, 'updated_fields': list(profile_data.keys())}
                )
                
                return ServiceResult(True, profile)
                
        except Exception as e:
            self.add_error(str(e), 'profile_update_error')
            return ServiceResult(False, None, str(e))

    def _validate_profile_data(self, data: Dict[str, Any]) -> bool:
        """Validate profile update data"""
        try:
            # Add specific validation rules
            if 'email' in data and not self._is_valid_email(data['email']):
                self.add_error("Invalid email format", 'validation_error')
                return False
            
            if 'phone' in data and not self._is_valid_phone(data['phone']):
                self.add_error("Invalid phone format", 'validation_error')
                return False
                
            return True
        except Exception as e:
            self.add_error(str(e), 'validation_error')
            return False

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format"""
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone))

class ProfileService(BaseService):
    """Enhanced profile management service"""

    def _validate(self, data: Dict[str, Any]) -> None:
        if 'profile' not in data:
            raise ValidationError("Profile is required")

    def update_avatar(self, profile: Profile, 
                     avatar_file: Any) -> ServiceResult[str]:
        """Update profile avatar with validation"""
        try:
            # Validate file
            if not self._validate_avatar_file(avatar_file):
                return ServiceResult(
                    False, None,
                    "Invalid avatar file",
                    {'validation_errors': self.get_errors()}
                )
                
            # Update avatar
            avatar_path = profile.update_avatar(avatar_file)
            
            LoggingService.log_info(
                f"Avatar updated for profile: {profile.id}",
                extra={'profile_id': profile.id}
            )
            
            return ServiceResult(True, avatar_path)
            
        except Exception as e:
            self.add_error(str(e), 'avatar_update_error')
            return ServiceResult(False, None, str(e))

    def _validate_avatar_file(self, file: Any) -> bool:
        """Validate avatar file"""
        try:
            if not file:
                self.add_error("No file provided", 'validation_error')
                return False
                
            # Check file size
            if file.size > 5 * 1024 * 1024:  # 5MB
                self.add_error("File too large", 'validation_error')
                return False
                
            # Check file type
            allowed_types = {'image/jpeg', 'image/png', 'image/gif'}
            if file.content_type not in allowed_types:
                self.add_error("Invalid file type", 'validation_error')
                return False
                
            return True
        except Exception as e:
            self.add_error(str(e), 'validation_error')
            return False

    def get_api_keys(self, profile: Profile) -> ServiceResult[Dict[str, str]]:
        """Get API keys with caching"""
        try:
            cache_key = f"api_keys:{profile.id}"
            api_keys = self.get_cached(cache_key)
            
            if not api_keys:
                api_keys = {
                    'gemini_key': profile.gemini_key,
                    'eleven_labs_key': profile.eleven_labs_key
                }
                self.set_cached(cache_key, api_keys)
                
            return ServiceResult(True, api_keys)
        except Exception as e:
            self.add_error(str(e), 'api_keys_error')
            return ServiceResult(False, None, str(e))

    def update_api_keys(self, profile: Profile,
                       gemini_key: Optional[str] = None,
                       eleven_labs_key: Optional[str] = None) -> ServiceResult[bool]:
        """Update API keys with validation"""
        try:
            with transaction.atomic():
                if gemini_key:
                    if not self._validate_api_key(gemini_key, 'gemini'):
                        return ServiceResult(
                            False, False,
                            "Invalid Gemini API key",
                            {'validation_errors': self.get_errors()}
                        )
                    profile.gemini_key = gemini_key
                    
                if eleven_labs_key:
                    if not self._validate_api_key(eleven_labs_key, 'eleven_labs'):
                        return ServiceResult(
                            False, False,
                            "Invalid Eleven Labs API key",
                            {'validation_errors': self.get_errors()}
                        )
                    profile.eleven_labs_key = eleven_labs_key
                    
                profile.save()
                
                # Clear cache
                self.clear_cached(f"api_keys:{profile.id}")
                
                LoggingService.log_info(
                    f"API keys updated for profile: {profile.id}",
                    extra={'profile_id': profile.id}
                )
                
                return ServiceResult(True, True)
                
        except Exception as e:
            self.add_error(str(e), 'api_keys_update_error')
            return ServiceResult(False, False, str(e))

    def _validate_api_key(self, key: str, provider: str) -> bool:
        """Validate API key format"""
        try:
            if not key:
                self.add_error(f"No {provider} API key provided", 'validation_error')
                return False
                
            # Add provider-specific validation
            if provider == 'gemini':
                if not key.startswith('AI') or len(key) != 39:
                    self.add_error("Invalid Gemini API key format", 'validation_error')
                    return False
                    
            elif provider == 'eleven_labs':
                if not len(key) == 32:
                    self.add_error("Invalid Eleven Labs API key format", 'validation_error')
                    return False
                    
            return True
        except Exception as e:
            self.add_error(str(e), 'validation_error')
            return False