import google.generativeai as genai
from typing import Dict, Optional, List, Any
import logging
from source.apps.core.services import BaseService, ServiceResult, LoggingService
from django.core.exceptions import ValidationError
from django.core.cache import cache
import json
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ScriptQualityMetrics:
    """Quality metrics for generated scripts"""
    engagement_score: float
    clarity_score: float
    seo_score: float
    audience_match: float
    word_count: int
    generated_at: datetime

class ContentGenerationUtility(BaseService):
    """Enhanced utility for generating content using Gemini AI"""

    def __init__(self, gemini_key: str):
        super().__init__()
        self.gemini_key = gemini_key
        self._configure_ai()
        
    def _configure_ai(self) -> None:
        """Configure Gemini AI with API key"""
        try:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-pro')
            LoggingService.log_info("Gemini AI configured successfully")
        except Exception as e:
            error_msg = f"Failed to configure Gemini AI: {str(e)}"
            self.add_error(error_msg, 'configuration_error')
            LoggingService.log_error(error_msg)

    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate input data"""
        required_fields = ['content_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def _get_prompt_template(self, content_type: str) -> ServiceResult[str]:
        """Get prompt template with caching"""
        try:
            cache_key = f'prompt_template_{content_type}'
            template = self.get_cached(cache_key)
            
            if not template:
                from apps.content.models import ContentType
                try:
                    content_type_obj = ContentType.objects.get(name=content_type)
                    template = content_type_obj.prompt_template
                    self.set_cached(cache_key, template, 3600)
                except ContentType.DoesNotExist:
                    error_msg = f"Content type {content_type} not found"
                    self.add_error(error_msg, 'template_error')
                    return ServiceResult(False, None, error_msg)
                    
            return ServiceResult(True, template)
        except Exception as e:
            error_msg = f"Failed to get prompt template: {str(e)}"
            self.add_error(error_msg, 'template_error')
            return ServiceResult(False, None, error_msg)

    def generate_script(self, content_type: str, 
                       custom_parameters: Optional[Dict] = None) -> ServiceResult[Dict[str, Any]]:
        """Generate script with quality metrics"""
        try:
            # Validate input
            validation_result = self.validate({'content_type': content_type})
            if validation_result.failed:
                return ServiceResult(False, None, validation_result.error)

            # Get template
            template_result = self._get_prompt_template(content_type)
            if template_result.failed:
                return template_result

            # Prepare prompt
            prompt = template_result.data
            if custom_parameters:
                prompt = prompt.format(**custom_parameters)

            # Generate content
            response = self.model.generate_content(prompt)
            if not response:
                error_msg = "Failed to generate content"
                self.add_error(error_msg, 'generation_error')
                return ServiceResult(False, None, error_msg)

            # Extract and analyze script
            script = response.text
            metrics = self._analyze_script_quality(script)
            
            result = {
                'script': script,
                'metrics': metrics.__dict__,
                'generated_at': datetime.now().isoformat(),
                'content_type': content_type,
                'parameters': custom_parameters
            }
            
            LoggingService.log_info(
                "Script generated successfully",
                extra={
                    'content_type': content_type,
                    'metrics': metrics.__dict__
                }
            )
            
            return ServiceResult(True, result)

        except Exception as e:
            error_msg = f"Script generation failed: {str(e)}"
            self.add_error(error_msg, 'generation_error')
            LoggingService.log_error(error_msg)
            return ServiceResult(False, None, error_msg)

    def _analyze_script_quality(self, script: str) -> ScriptQualityMetrics:
        """Analyze script quality metrics"""
        try:
            # Calculate basic metrics
            words = script.split()
            word_count = len(words)
            
            # Calculate engagement score based on various factors
            engagement_score = self._calculate_engagement_score(script)
            
            # Calculate clarity score
            clarity_score = self._calculate_clarity_score(script)
            
            # Calculate SEO score
            seo_score = self._calculate_seo_score(script)
            
            # Calculate audience match score
            audience_match = self._calculate_audience_match(script)
            
            return ScriptQualityMetrics(
                engagement_score=engagement_score,
                clarity_score=clarity_score,
                seo_score=seo_score,
                audience_match=audience_match,
                word_count=word_count,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            LoggingService.log_error(f"Failed to analyze script quality: {str(e)}")
            return ScriptQualityMetrics(0.0, 0.0, 0.0, 0.0, 0, datetime.now())

    def _calculate_engagement_score(self, script: str) -> float:
        """Calculate engagement score based on various factors"""
        try:
            # Implementation of engagement scoring logic
            return 0.85  # Placeholder
        except Exception as e:
            LoggingService.log_error(f"Failed to calculate engagement score: {str(e)}")
            return 0.0

    def _calculate_clarity_score(self, script: str) -> float:
        """Calculate clarity score"""
        try:
            # Implementation of clarity scoring logic
            return 0.90  # Placeholder
        except Exception as e:
            LoggingService.log_error(f"Failed to calculate clarity score: {str(e)}")
            return 0.0

    def _calculate_seo_score(self, script: str) -> float:
        """Calculate SEO optimization score"""
        try:
            # Implementation of SEO scoring logic
            return 0.88  # Placeholder
        except Exception as e:
            LoggingService.log_error(f"Failed to calculate SEO score: {str(e)}")
            return 0.0

    def _calculate_audience_match(self, script: str) -> float:
        """Calculate audience match score"""
        try:
            # Implementation of audience matching logic
            return 0.92  # Placeholder
        except Exception as e:
            LoggingService.log_error(f"Failed to calculate audience match: {str(e)}")
            return 0.0

    def batch_generate_scripts(self, configs: List[Dict[str, Any]]) -> ServiceResult[List[Dict[str, Any]]]:
        """Generate multiple scripts in parallel"""
        try:
            with ThreadPoolExecutor() as executor:
                futures = []
                for config in configs:
                    future = executor.submit(
                        self.generate_script,
                        config['content_type'],
                        config.get('parameters')
                    )
                    futures.append(future)
                
                results = []
                for future in futures:
                    result = future.result()
                    results.append(result.data if result.success else None)
                
            successful = len([r for r in results if r is not None])
            LoggingService.log_info(
                f"Batch script generation completed: {successful}/{len(configs)} successful"
            )
            
            return ServiceResult(True, results)
            
        except Exception as e:
            error_msg = f"Batch script generation failed: {str(e)}"
            self.add_error(error_msg, 'batch_error')
            LoggingService.log_error(error_msg)
            return ServiceResult(False, None, error_msg)