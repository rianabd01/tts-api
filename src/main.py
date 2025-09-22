from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import tempfile
import shutil
import hashlib
import logging
import time
import threading
from pathlib import Path

from config import settings
from tts_service import tts_service, TTS_AVAILABLE

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A powerful Text-to-Speech API using Coqui TTS with voice cloning capabilities",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to check TTS availability
@app.on_event("startup")
async def startup_event():
    """Check TTS service availability on startup"""
    if not TTS_AVAILABLE or tts_service is None:
        logger.error("❌ Coqui TTS is not available!")
        logger.error("Please upgrade to Python 3.11+ or use Docker for compatibility.")
        raise RuntimeError("TTS service is required but not available")
    else:
        logger.info("✅ TTS Service is ready and available")
        # Ensure output directories exist
        Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs",
        "endpoints": {
            "text_to_speech": "/tts",
            "available_models": "/models",
            "model_info": "/models/{model_name}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not TTS_AVAILABLE or tts_service is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "TTS service not available",
                "tts_available": False
            }
        )
    
    return {
        "status": "healthy",
        "device": tts_service.device,
        "loaded_models": len(tts_service.models),
        "tts_engine": "coqui_tts",
        "tts_available": True,
        "version": settings.app_version
    }

@app.get("/compatibility")
async def compatibility_check():
    """Check system compatibility"""
    import sys
    
    compatibility_info = {
        "python_version": sys.version,
        "tts_available": TTS_AVAILABLE,
        "tts_service_ready": tts_service is not None,
        "tts_engine": "coqui_tts",
        "device": tts_service.device if tts_service else "unknown",
        "status": "ready" if TTS_AVAILABLE and tts_service else "not_ready",
        "recommendations": [
            "Coqui TTS is active" if TTS_AVAILABLE else "Coqui TTS failed to load",
            "Voice cloning available" if TTS_AVAILABLE else "Upgrade to Python 3.11+ or use Docker",
            "Full TTS functionality available" if TTS_AVAILABLE else "TTS functionality limited"
        ]
    }
    
    return compatibility_info

@app.get("/models", response_model=List[str])
async def get_available_models():
    """Get list of available TTS models"""
    if not TTS_AVAILABLE or tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        models = tts_service.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")

@app.get("/models/{model_name:path}", response_model=Dict[str, Any])
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    if not TTS_AVAILABLE or tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        info = tts_service.get_model_info(model_name)
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.post("/tts")
async def voice_clone_tts(
    text: str = Form(..., description="Text to convert to speech"),
    model_name: str = Form("tts_models/multilingual/multi-dataset/xtts_v2", description="TTS model to use"), 
    language: str = Form("en", description="Language code"),
    output_format: str = Form("wav", description="Output audio format"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Text-to-speech with voice cloning using static harvard.wav - returns audio file for download"""
    
    # Check TTS service availability
    if not TTS_AVAILABLE or tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    # Validate text length
    if len(text) > settings.max_text_length:
        raise HTTPException(
            status_code=400, 
            detail=f"Text too long. Maximum length is {settings.max_text_length} characters"
        )
    
    # Use static harvard.wav file for voice cloning
    harvard_wav_path = os.path.join(os.path.dirname(__file__), "harvard.wav")
    if not os.path.exists(harvard_wav_path):
        raise HTTPException(status_code=500, detail="Reference audio file (harvard.wav) not found")
    
    # Create temporary directory for this request
    temp_dir = tempfile.mkdtemp(prefix="tts_")
    temp_speaker_path = None
    temp_output_path = None
    
    try:
        # Set output path
        temp_output_path = os.path.join(temp_dir, f"output.{output_format}")
        
        # Generate safe filename for download
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        timestamp = int(time.time())
        output_filename = f"tts_harvard_{language}_{text_hash}_{timestamp}.{output_format}"
        
        # Load TTS model
        tts = tts_service.load_model(model_name)
        
        # Synthesize speech using harvard.wav for voice cloning
        if "xtts" in model_name.lower():
            tts.tts_to_file(
                text=text,
                speaker_wav=harvard_wav_path,
                language=language or "en",
                file_path=temp_output_path
            )
        else:
            tts.tts_with_vc_to_file(
                text=text,
                speaker_wav=harvard_wav_path,
                file_path=temp_output_path
            )
        
        # Schedule cleanup of temp directory
        def cleanup_temp_directory():
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
        
        background_tasks.add_task(cleanup_temp_directory)
        
        logger.info(f"Generated audio file: {output_filename}")
        
        # Return the audio file for download
        return FileResponse(
            path=temp_output_path,
            filename=output_filename,
            media_type=f"audio/{output_format}",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{output_filename}"
            }
        )
        
    except ValueError as e:
        # Clean up on error
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up on error
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Voice cloning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

@app.delete("/cleanup")
async def cleanup_files(max_age_hours: int = 24):
    """Manually trigger cleanup of old files"""
    if not TTS_AVAILABLE or tts_service is None:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        tts_service.cleanup_old_files(max_age_hours)
        return {"message": "Cleanup completed successfully"}
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": "Validation Error", "details": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error", "details": "An unexpected error occurred"}
    )

# Hourly cleanup scheduler
def start_cleanup_scheduler():
    """Start background cleanup scheduler"""
    def cleanup_task():
        while True:
            try:
                time.sleep(3600)  # Wait 1 hour
                if os.path.exists(settings.output_dir) and tts_service:
                    current_time = time.time()
                    files_cleaned = 0
                    for filename in os.listdir(settings.output_dir):
                        if filename.endswith('.wav'):
                            file_path = os.path.join(settings.output_dir, filename)
                            if os.path.isfile(file_path):
                                file_age = current_time - os.path.getctime(file_path)
                                if file_age > 3600:  # Older than 1 hour
                                    try:
                                        os.remove(file_path)
                                        files_cleaned += 1
                                    except Exception as e:
                                        logger.error(f"Failed to remove {filename}: {e}")
                    
                    if files_cleaned > 0:
                        logger.info(f"🧹 Hourly cleanup: removed {files_cleaned} old files")
                        
            except Exception as e:
                logger.error(f"Error in hourly cleanup: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("⏰ Started hourly cleanup scheduler")

# Start cleanup scheduler when server starts
if TTS_AVAILABLE and tts_service:
    start_cleanup_scheduler()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )