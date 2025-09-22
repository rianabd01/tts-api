import torch
import os
import hashlib
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import soundfile as sf
from config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive compatibility patch for Coqui TTS
try:
    import sys
    import types
    import warnings
    
    # Patch bangla module compatibility
    bangla_mock = types.ModuleType('bangla')
    def mock_get_date(*args, **kwargs):
        return ""
    bangla_mock.get_date = mock_get_date
    sys.modules['bangla'] = bangla_mock
    
    # Set environment variable for PyTorch compatibility
    os.environ['TORCH_DISABLE_WEIGHTS_ONLY'] = '1'
    
    # Comprehensive PyTorch safe globals setup
    if hasattr(torch.serialization, 'add_safe_globals'):
        try:
            xtts_classes = []
            
            # Import and register all XTTS-related classes
            try:
                from TTS.tts.configs.xtts_config import XttsConfig
                xtts_classes.append(XttsConfig)
            except ImportError:
                pass
                
            try:
                from TTS.tts.models.xtts import XttsAudioConfig
                xtts_classes.append(XttsAudioConfig)
            except ImportError:
                pass
                
            try:
                from TTS.tts.configs.shared_configs import BaseDatasetConfig, BaseAudioConfig
                xtts_classes.extend([BaseDatasetConfig, BaseAudioConfig])
            except ImportError:
                pass
                
            try:
                from TTS.tts.configs.vits_config import VitsConfig
                xtts_classes.append(VitsConfig)
            except ImportError:
                pass
                
            try:
                from TTS.vocoder.configs.hifigan_config import HifiganConfig
                xtts_classes.append(HifiganConfig)
            except ImportError:
                pass
            
            # Register all discovered classes
            if xtts_classes:
                torch.serialization.add_safe_globals(xtts_classes)
                logger.info(f"✅ Registered {len(xtts_classes)} XTTS classes for PyTorch compatibility")
                
        except Exception as e:
            logger.warning(f"Could not configure PyTorch safe globals: {e}")
    
    # Import TTS after compatibility setup
    from TTS.api import TTS
    TTS_AVAILABLE = True
    logger.info("✅ Coqui TTS loaded successfully with compatibility patches")
    
except Exception as e:
    TTS_AVAILABLE = False
    TTS = None
    logger.error(f"❌ Failed to load Coqui TTS: {e}")
    logger.error("Please ensure you're using Python 3.11+ or run with Docker for full compatibility")

class TTSService:
    def __init__(self):
        self.models: Dict[str, TTS] = {}
        self.device = self._get_device()
        logger.info(f"TTS Service initialized with device: {self.device}")
        
        if not TTS_AVAILABLE:
            logger.error("Coqui TTS is not available!")
            logger.error("This service requires Coqui TTS to function properly")
            logger.error("Please upgrade to Python 3.11+ or use Docker")
            raise RuntimeError("Coqui TTS is required but not available")
        else:
            logger.info("Coqui TTS loaded successfully - ready for synthesis")
    
    def _get_device(self) -> str:
        """Determine the best device to use"""
        if settings.device == "auto":
            if torch is not None and torch.cuda.is_available():
                logger.info("CUDA available, using GPU")
                return "cuda"
            else:
                logger.info("Using CPU device")
                return "cpu"
        return settings.device
    
    def _get_model_key(self, model_name: str) -> str:
        """Generate a unique key for model caching"""
        return hashlib.md5(model_name.encode()).hexdigest()
    
    def load_model(self, model_name: str) -> TTS:
        """Load and cache TTS model with enhanced error handling"""
        if not TTS_AVAILABLE:
            raise ValueError("Coqui TTS is not available. Please upgrade Python or use Docker.")
            
        model_key = self._get_model_key(model_name)
        
        if model_key not in self.models:
            try:
                logger.info(f"Loading TTS model: {model_name}")
                
                # Enhanced handling for XTTSv2 models
                if "xtts" in model_name.lower():
                    logger.info("Applying XTTSv2-specific compatibility patches")
                    
                    # Import warnings module for patching
                    import warnings
                    
                    # Store original functions for restoration
                    original_load = torch.load
                    original_warn = warnings.warn
                    
                    def patched_load(*args, **kwargs):
                        # Force weights_only=False for XTTS models
                        kwargs['weights_only'] = False
                        return original_load(*args, **kwargs)
                    
                    def suppress_warnings(*args, **kwargs):
                        # Suppress PyTorch warnings about weights_only
                        if args and 'weights_only' in str(args[0]):
                            return
                        return original_warn(*args, **kwargs)
                    
                    # Apply patches
                    torch.load = patched_load
                    warnings.warn = suppress_warnings
                    
                    # Set environment variable
                    old_env = os.environ.get('TORCH_DISABLE_WEIGHTS_ONLY')
                    os.environ['TORCH_DISABLE_WEIGHTS_ONLY'] = '1'
                    
                    try:
                        tts = TTS(model_name).to(self.device)
                        logger.info(f"✅ XTTSv2 model loaded successfully: {model_name}")
                        
                    finally:
                        # Restore original functions
                        torch.load = original_load
                        warnings.warn = original_warn
                        
                        # Restore environment
                        if old_env is not None:
                            logger.info("Restoring TORCH_DISABLE_WEIGHTS_ONLY")
                            os.environ['TORCH_DISABLE_WEIGHTS_ONLY'] = old_env
                        else:
                            logger.info("TORCH_DISABLE_WEIGHTS_ONLY not set")
                            os.environ.pop('TORCH_DISABLE_WEIGHTS_ONLY', None)
                else:
                    # Regular model loading
                    tts = TTS(model_name).to(self.device)
                    logger.info(f"✅ Model loaded successfully: {model_name}")
                
                self.models[model_key] = tts
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                if "xtts" in model_name.lower():
                    logger.error("💡 XTTSv2 troubleshooting:")
                    logger.error("🐳 Try Docker: docker-compose up --build")
                    logger.error("🔄 Or use alternative models: tts_models/en/ljspeech/tacotron2-DDC")
                raise ValueError(f"Failed to load model {model_name}: {str(e)}")
        
        return self.models[model_key]
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not TTS_AVAILABLE:
            raise ValueError("Coqui TTS is not available. Cannot retrieve model list.")
            
        try:
            tts = TTS()
            return tts.list_models()
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return settings.available_models
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        try:
            tts = self.load_model(model_name)
            info = {
                "model_name": model_name,
                "device": self.device,
                "speakers": getattr(tts, 'speakers', None),
                "languages": getattr(tts, 'languages', None),
                "is_multi_speaker": hasattr(tts, 'speakers') and tts.speakers is not None,
                "is_multi_lingual": hasattr(tts, 'languages') and tts.languages is not None,
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {str(e)}")
            raise ValueError(f"Failed to get model info: {str(e)}")
    
    def synthesize_speech(
        self,
        text: str,
        model_name: Optional[str] = None,
        speaker: Optional[str] = None,
        speaker_wav: Optional[str] = None,
        language: Optional[str] = None,
        output_format: str = "wav"
    ) -> str:
        """Synthesize speech from text using Coqui TTS"""
        
        # Validate input
        if len(text) > settings.max_text_length:
            raise ValueError(f"Text too long. Maximum length is {settings.max_text_length} characters")
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not TTS_AVAILABLE:
            raise ValueError("Coqui TTS is not available. Please upgrade to Python 3.11+ or use Docker.")
        
        return self._synthesize_with_coqui(text, model_name, speaker, speaker_wav, language, output_format)
    

    
    def _synthesize_with_coqui(
        self, text: str, model_name: Optional[str], speaker: Optional[str], 
        speaker_wav: Optional[str], language: Optional[str], output_format: str
    ) -> str:
        """Synthesize speech using Coqui TTS"""
        # Use default model if none specified
        if model_name is None:
            model_name = settings.default_model
        
        # Validate model
        if model_name not in settings.available_models:
            try:
                available_models = self.get_available_models()
                if model_name not in available_models:
                    raise ValueError(f"Model {model_name} not available")
            except Exception:
                logger.warning(f"Could not verify model {model_name}, proceeding anyway")
        
        # Load model
        tts = self.load_model(model_name)
        
        # Generate unique filename for caching
        text_hash = hashlib.md5(f"{text}{model_name}{speaker}{language}".encode()).hexdigest()
        output_filename = f"tts_{text_hash}.{output_format}"
        output_path = os.path.join(settings.output_dir, output_filename)
        
        # Check if file already exists (caching)
        if os.path.exists(output_path):
            logger.info(f"Using cached audio file: {output_filename}")
            return output_path
        
        try:
            # Get model information for synthesis strategy
            model_info = self.get_model_info(model_name)
            
            if speaker_wav:
                # Voice cloning with speaker wav file
                if not os.path.exists(speaker_wav):
                    raise ValueError(f"Speaker wav file not found: {speaker_wav}")
                
                if "xtts" in model_name.lower():
                    # XTTS model supports direct voice cloning
                    tts.tts_to_file(
                        text=text,
                        speaker_wav=speaker_wav,
                        language=language or "en",
                        file_path=output_path
                    )
                else:
                    # Use voice conversion for other models
                    tts.tts_with_vc_to_file(
                        text=text,
                        speaker_wav=speaker_wav,
                        file_path=output_path
                    )
            elif speaker and model_info.get("is_multi_speaker"):
                # Multi-speaker model with speaker ID
                tts.tts_to_file(
                    text=text,
                    speaker=speaker,
                    language=language,
                    file_path=output_path
                )
            else:
                # Single speaker model
                if hasattr(tts, 'tts_to_file'):
                    if language and model_info.get("is_multi_lingual"):
                        tts.tts_to_file(text=text, language=language, file_path=output_path)
                    else:
                        tts.tts_to_file(text=text, file_path=output_path)
                else:
                    # Fallback for models without tts_to_file
                    wav = tts.tts(text=text)
                    sf.write(output_path, wav, 22050)
            
            logger.info(f"Speech synthesized successfully: {output_filename}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {str(e)}")
            raise ValueError(f"Failed to synthesize speech: {str(e)}")

    def voice_conversion(
        self,
        source_wav: str,
        target_wav: str,
        model_name: str = "voice_conversion_models/multilingual/vctk/freevc24",
        output_format: str = "wav"
    ) -> str:
        """Convert voice in source audio to target voice"""
        
        # Validate input files
        if not os.path.exists(source_wav):
            raise ValueError(f"Source wav file not found: {source_wav}")
        
        if not os.path.exists(target_wav):
            raise ValueError(f"Target wav file not found: {target_wav}")
        
        # Load voice conversion model
        try:
            tts = TTS(model_name).to(self.device)
        except Exception as e:
            logger.error(f"Failed to load voice conversion model: {str(e)}")
            raise ValueError(f"Failed to load voice conversion model: {str(e)}")
        
        # Generate output filename
        source_hash = hashlib.md5(f"{source_wav}{target_wav}{model_name}".encode()).hexdigest()
        output_filename = f"vc_{source_hash}.{output_format}"
        output_path = os.path.join(settings.output_dir, output_filename)
        
        # Check if file already exists (caching)
        if os.path.exists(output_path):
            logger.info(f"Using cached voice conversion file: {output_filename}")
            return output_path
        
        try:
            # Perform voice conversion
            tts.voice_conversion_to_file(
                source_wav=source_wav,
                target_wav=target_wav,
                file_path=output_path
            )
            
            logger.info(f"Voice conversion completed: {output_filename}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to perform voice conversion: {str(e)}")
            raise ValueError(f"Failed to perform voice conversion: {str(e)}")
    
    def ensure_output_directory(self):
        """Ensure the output directory exists"""
        os.makedirs(settings.output_dir, exist_ok=True)
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old generated files"""
        import time
        current_time = time.time()
        cleaned_count = 0
        
        if not os.path.exists(settings.output_dir):
            return
        
        for filename in os.listdir(settings.output_dir):
            file_path = os.path.join(settings.output_dir, filename)
            if os.path.isfile(file_path):
                try:
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > max_age_hours * 3600:  # Convert hours to seconds
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove old file {filename}: {str(e)}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old files")

# Initialize TTS service - only if Coqui TTS is available
if TTS_AVAILABLE:
    try:
        tts_service = TTSService()
        logger.info("✅ TTS Service initialized successfully with Coqui TTS")
    except Exception as e:
        logger.error(f"❌ Failed to initialize TTS Service: {e}")
        tts_service = None
else:
    tts_service = None
    logger.error("❌ TTS Service not available - Coqui TTS failed to load")