import requests
from typing import Optional, Dict, Any, List
import logging
from source.apps.core.services import BaseService, ServiceResult, LoggingService
from django.core.exceptions import ValidationError
from django.core.cache import cache
import json
import os
import concurrent.futures
import librosa
import numpy as np
import io
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class VoiceQualityMetrics:
    """Quality metrics for generated voiceovers"""
    duration: float
    tempo: float
    rms_energy: float
    zero_crossings: int
    generated_at: datetime

class VoiceoverGenerationUtility(BaseService):
    """Enhanced utility for generating voiceovers using Eleven Labs API"""

    BASE_URL = "https://api.elevenlabs.io/v1"
    DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        })

    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate input data"""
        if 'text' not in data:
            raise ValidationError("Text is required for voiceover generation")
        if len(data['text']) > 5000:
            raise ValidationError("Text exceeds maximum length of 5000 characters")

    def generate_voiceover(self, text: str, voice_id: Optional[str] = None,
                          model_id: str = "eleven_multilingual_v2") -> ServiceResult[Dict[str, Any]]:
        """Generate voiceover with quality metrics"""
        try:
            # Validate input
            validation_result = self.validate({'text': text})
            if validation_result.failed:
                return ServiceResult(False, None, validation_result.error)

            voice_id = voice_id or self.DEFAULT_VOICE_ID
            url = f"{self.BASE_URL}/text-to-speech/{voice_id}"

            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75
                }
            }

            response = self.session.post(url, json=data)
            if not response.ok:
                error_msg = f"Voiceover generation failed: {response.text}"
                self.add_error(error_msg, 'generation_error')
                return ServiceResult(False, None, error_msg)

            # Convert response to audio array
            audio_bytes = io.BytesIO(response.content)
            metrics = self._analyze_audio_quality(audio_bytes)

            result = {
                'audio_data': response.content,
                'metrics': metrics.__dict__,
                'generated_at': datetime.now().isoformat(),
                'voice_id': voice_id,
                'model_id': model_id
            }

            LoggingService.log_info(
                "Voiceover generated successfully",
                extra={
                    'voice_id': voice_id,
                    'model_id': model_id,
                    'metrics': metrics.__dict__
                }
            )

            return ServiceResult(True, result)

        except Exception as e:
            error_msg = f"Voiceover generation failed: {str(e)}"
            self.add_error(error_msg, 'generation_error')
            LoggingService.log_error(error_msg)
            return ServiceResult(False, None, error_msg)

    def _analyze_audio_quality(self, audio_bytes: io.BytesIO) -> VoiceQualityMetrics:
        """Analyze audio quality metrics"""
        try:
            # Load audio
            y, sr = librosa.load(audio_bytes)
            
            # Calculate metrics
            duration = librosa.get_duration(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            rms_energy = np.sqrt(np.mean(y**2))
            zero_crossings = sum(librosa.zero_crossings(y))
            
            return VoiceQualityMetrics(
                duration=duration,
                tempo=tempo,
                rms_energy=float(rms_energy),
                zero_crossings=int(zero_crossings),
                generated_at=datetime.now()
            )
            
        except Exception as e:
            LoggingService.log_error(f"Failed to analyze audio quality: {str(e)}")
            return VoiceQualityMetrics(0.0, 0.0, 0.0, 0, datetime.now())

    def batch_generate_voiceovers(self, 
                                texts: List[Dict[str, Any]]) -> ServiceResult[List[Dict[str, Any]]]:
        """Generate multiple voiceovers in parallel"""
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for config in texts:
                    future = executor.submit(
                        self.generate_voiceover,
                        config['text'],
                        config.get('voice_id'),
                        config.get('model_id', "eleven_multilingual_v2")
                    )
                    futures.append(future)
                
                results = []
                for future in futures:
                    result = future.result()
                    results.append(result.data if result.success else None)
                
            successful = len([r for r in results if r is not None])
            LoggingService.log_info(
                f"Batch voiceover generation completed: {successful}/{len(texts)} successful"
            )
            
            return ServiceResult(True, results)
            
        except Exception as e:
            error_msg = f"Batch voiceover generation failed: {str(e)}"
            self.add_error(error_msg, 'batch_error')
            LoggingService.log_error(error_msg)
            return ServiceResult(False, None, error_msg)

    def optimize_voice_settings(self, text: str, target_metrics: Dict[str, float],
                              voice_id: Optional[str] = None) -> ServiceResult[Dict[str, Any]]:
        """Optimize voice settings based on target metrics"""
        try:
            # Generate initial voiceover
            initial_result = self.generate_voiceover(text, voice_id)
            if initial_result.failed:
                return initial_result

            current_metrics = initial_result.data['metrics']
            
            # Calculate optimal settings
            optimal_settings = self._calculate_optimal_settings(
                current_metrics,
                target_metrics
            )
            
            # Generate optimized voiceover
            voice_id = voice_id or self.DEFAULT_VOICE_ID
            url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": optimal_settings
            }
            
            response = self.session.post(url, json=data)
            if not response.ok:
                error_msg = f"Optimized voiceover generation failed: {response.text}"
                self.add_error(error_msg, 'optimization_error')
                return ServiceResult(False, None, error_msg)
                
            audio_bytes = io.BytesIO(response.content)
            metrics = self._analyze_audio_quality(audio_bytes)
            
            result = {
                'audio_data': response.content,
                'metrics': metrics.__dict__,
                'settings': optimal_settings,
                'generated_at': datetime.now().isoformat()
            }
            
            LoggingService.log_info(
                "Voice settings optimized successfully",
                extra={
                    'voice_id': voice_id,
                    'target_metrics': target_metrics,
                    'achieved_metrics': metrics.__dict__
                }
            )
            
            return ServiceResult(True, result)
            
        except Exception as e:
            error_msg = f"Voice optimization failed: {str(e)}"
            self.add_error(error_msg, 'optimization_error')
            LoggingService.log_error(error_msg)
            return ServiceResult(False, None, error_msg)

    def _calculate_optimal_settings(self, current: Dict[str, Any], 
                                  target: Dict[str, float]) -> Dict[str, float]:
        """Calculate optimal voice settings based on metrics"""
        try:
            # Implement optimization logic here
            # This is a simplified example
            return {
                "stability": 0.8,
                "similarity_boost": 0.7,
                "style": 0.6,
                "use_speaker_boost": True
            }
        except Exception as e:
            LoggingService.log_error(f"Failed to calculate optimal settings: {str(e)}")
            return {
                "stability": 0.75,
                "similarity_boost": 0.75
            }