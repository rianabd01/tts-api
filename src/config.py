from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Coqui TTS API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # TTS settings
    default_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    device: str = "auto"  # auto, cpu, cuda
    cache_dir: str = "./cache"
    output_dir: str = "./outputs"
    
    # Supported models - comprehensive list
    available_models: List[str] = [
        # English models
        "tts_models/en/ljspeech/tacotron2-DDC",
        "tts_models/en/ljspeech/glow-tts",
        "tts_models/en/ljspeech/speedy-speech",
        "tts_models/en/ljspeech/tacotron2-DCA",
        "tts_models/en/ljspeech/vits",
        
        # Multi-speaker models
        "tts_models/en/vctk/vits",
        "tts_models/en/vctk/fast_pitch",
        
        # Multilingual models
        "tts_models/multilingual/multi-dataset/xtts_v2",
        "tts_models/multilingual/multi-dataset/your_tts",
        "tts_models/multilingual/multi-dataset/bark",
        
        # Voice conversion models
        "voice_conversion_models/multilingual/vctk/freevc24",
    ]
    
    # API settings
    max_text_length: int = 1000
    allowed_audio_formats: List[str] = ["wav", "mp3", "flac"]
    
    # Performance settings
    max_workers: int = 1
    cleanup_interval_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)