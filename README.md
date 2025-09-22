# Coqui TTS API

A powerful, production-ready Text-to-Speech API built with FastAPI and Coqui TTS, providing high-quality speech synthesis and voice cloning capabilities through REST API endpoints.

## ✨ Features

- 🎯 **Text-to-Speech**: Convert text to speech using various TTS models
- 🎭 **Voice Cloning**: Clone voices from uploaded audio samples using XTTSv2
- 🌍 **Multi-language Support**: Support for 100+ languages
- 🎙️ **Multi-speaker Models**: Support for multiple speakers
- 🚀 **Fast API**: RESTful API with automatic documentation
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 📁 **Smart Caching**: Intelligent caching for generated audio files
- 🧹 **Auto Cleanup**: Automatic cleanup of old files
- 🔧 **Configurable**: Flexible configuration system

## 🚀 Quick Start

### Option 1: Using Docker (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd tts
```

2. **Start with Docker Compose**:

**For most systems (x86_64):**
```bash
# Using the startup script
./start.sh

# Or manually
docker-compose up --build
```

**For ARM64/Apple Silicon (M1/M2 Macs):**
```bash
# Using the ARM64-optimized startup script
./start-arm64.sh

# Or manually
DOCKERFILE=Dockerfile.arm64 docker-compose up --build
```

3. **Access the API**:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Option 2: Local Installation (Python 3.11+ Required)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the application**:
```bash
python main.py
```

## 📋 System Requirements

### For Docker (Recommended)
- Docker 20.0+
- Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum

### For Local Installation
- Python 3.11+ (required for XTTSv2 compatibility)
- 4GB RAM minimum
- PyTorch 2.0+

## 🛠️ Troubleshooting

### Common Docker Build Issues

**1. ARM64/Apple Silicon (M1/M2) Build Failures:**
```bash
# Use the ARM64-optimized Dockerfile
./start-arm64.sh
# OR
DOCKERFILE=Dockerfile.arm64 docker-compose up --build
```

**2. Rust Compiler Errors (sudachipy):**
The ARM64 Dockerfile automatically handles this by installing dependencies individually.

**3. Memory Issues During Build:**
```bash
# Increase Docker memory limit to 4GB+
# Or use the ARM64 version which has optimized dependency installation
```

**4. PyTorch Compatibility Issues:**
The Dockerfile pins PyTorch to version 2.1.0 for stability.

### Runtime Issues

**1. Health Check Failures:**
- Wait 2-3 minutes for the first model to load
- Check logs: `docker-compose logs -f coqui-tts-api`

**2. Voice Cloning Errors:**
- Ensure audio files are in supported formats (WAV, MP3, FLAC)
- Check file size (keep under 10MB for best performance)

**3. Memory Issues:**
- Use CPU mode for lower memory usage
- Restart the container if memory usage grows

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Basic Text-to-Speech

**POST** `/tts`

Convert text to speech using default or specified models.

```bash
curl -X POST "http://localhost:8000/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the text-to-speech system!",
    "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
    "language": "en",
    "output_format": "wav"
  }'
```

**Response:**
```json
{
  "success": true,
  "filename": "tts_abc123.wav",
  "message": "Speech synthesized successfully",
  "download_url": "/download/tts_abc123.wav"
}
```

### 2. Voice Cloning

**POST** `/tts/clone`

Generate speech that mimics the voice from an uploaded audio sample.

```bash
curl -X POST "http://localhost:8000/tts/clone" \
  -F "speaker_wav=@/path/to/voice_sample.wav" \
  -F "text=Hello, this is voice cloning in action!" \
  -F "model_name=tts_models/multilingual/multi-dataset/xtts_v2" \
  -F "language=en"
```

### 3. Voice Conversion

**POST** `/tts/voice-conversion`

Convert the voice in a source audio file to match a target voice.

```bash
curl -X POST "http://localhost:8000/tts/voice-conversion" \
  -F "source_wav=@/path/to/source.wav" \
  -F "target_wav=@/path/to/target_voice.wav" \
  -F "model_name=voice_conversion_models/multilingual/vctk/freevc24"
```

### 4. Available Models

**GET** `/models`

Get list of all available TTS models.

```bash
curl -X GET "http://localhost:8000/models"
```

### 5. Model Information

**GET** `/models/{model_name}`

Get detailed information about a specific model.

```bash
curl -X GET "http://localhost:8000/models/tts_models/en/ljspeech/tacotron2-DDC"
```

### 6. Download Generated Audio

**GET** `/download/{filename}`

Download the generated audio file.

```bash
curl -X GET "http://localhost:8000/download/tts_abc123.wav" --output speech.wav
```

### 7. Health Check

**GET** `/health`

Check API health and status.

```bash
curl -X GET "http://localhost:8000/health"
```

## Supported Models

### TTS Models

- **English**: `tts_models/en/ljspeech/tacotron2-DDC`, `tts_models/en/ljspeech/glow-tts`
- **Multilingual**: `tts_models/multilingual/multi-dataset/xtts_v2`
- **Multi-speaker**: `tts_models/en/vctk/vits`
- **Fairseq Models**: `tts_models/<lang-code>/fairseq/vits` (1100+ languages)

### Voice Conversion Models

- `voice_conversion_models/multilingual/vctk/freevc24`
- `voice_conversion_models/multilingual/multi-dataset/knnvc`
- `voice_conversion_models/multilingual/multi-dataset/openvoice_v1`
- `voice_conversion_models/multilingual/multi-dataset/openvoice_v2`

## Configuration

Create a `.env` file (copy from `.env.example`) to customize settings:

```env
# Application settings
APP_NAME="Coqui TTS API"
DEBUG=false

# Server settings
HOST="0.0.0.0"
PORT=8000

# TTS settings
DEFAULT_MODEL="tts_models/en/ljspeech/tacotron2-DDC"
DEVICE="auto"  # auto, cpu, cuda
MAX_TEXT_LENGTH=1000
```

## Usage Examples

### Python Client Example

```python
import requests
import json

# Basic TTS
response = requests.post("http://localhost:8000/tts", 
    json={
        "text": "Hello world!",
        "model_name": "tts_models/en/ljspeech/tacotron2-DDC"
    }
)

if response.status_code == 200:
    result = response.json()
    # Download the audio file
    audio_response = requests.get(f"http://localhost:8000{result['download_url']}")
    with open("output.wav", "wb") as f:
        f.write(audio_response.content)
    print("Audio saved as output.wav")

# Voice cloning with file upload
files = {"speaker_wav": open("voice_sample.wav", "rb")}
data = {
    "text": "This is cloned voice speaking",
    "language": "en"
}
response = requests.post("http://localhost:8000/tts/clone", files=files, data=data)
```

### JavaScript/Node.js Example

```javascript
// Basic TTS
fetch('http://localhost:8000/tts', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        text: "Hello from JavaScript!",
        model_name: "tts_models/en/ljspeech/tacotron2-DDC"
    })
})
.then(response => response.json())
.then(data => {
    console.log('TTS Response:', data);
    // Download the audio file
    return fetch(`http://localhost:8000${data.download_url}`);
})
.then(response => response.blob())
.then(blob => {
    // Handle the audio blob (play, save, etc.)
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.play();
});
```

## GPU Support

To enable GPU acceleration:

1. Install CUDA-compatible PyTorch:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. Set device in configuration:
```env
DEVICE=cuda
```

3. For Docker, use nvidia-docker or update docker-compose.yml with GPU support.

## Performance Tips

1. **Model Caching**: Models are automatically cached after first load
2. **Audio Caching**: Generated audio files are cached based on input parameters
3. **Cleanup**: Old files are automatically cleaned up (configurable)
4. **GPU Usage**: Use GPU for faster inference when available

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce model size or use CPU mode
2. **Audio Format Issues**: Ensure input audio files are in supported formats
3. **Model Download Failures**: Check internet connection and retry

### Logs

Check application logs for detailed error information:

```bash
# Docker
docker-compose logs -f coqui-tts-api

# Local
python main.py  # Logs will appear in terminal
```

## Development

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Testing

Use the interactive documentation at `http://localhost:8000/docs` to test all endpoints.

## License

This project uses Coqui TTS which is licensed under MPL 2.0. Please check the original repository for license details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the logs for error details
- Ensure all dependencies are properly installed
- Verify model availability and compatibility

## Changelog

### v1.0.0
- Initial release
- Basic TTS functionality
- Voice cloning support
- Voice conversion support
- Docker deployment
- Comprehensive API documentation