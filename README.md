# Text-to-Speech Service

Text-to-speech conversion with voice cloning support.

## Features
- Auto detect language
- High-quality Text-to-Speech
- 17 languages supported
- REST API

## Quick Start

### Requirements
- Python 3.11

### Development
```bash
make install
make dev || make run
```

### Using Docker
```bash
# Clone and start the service
git clone <repository-url>
cd tts
docker compose up -d
```

### API Usage
```bash
# Generate speech from text
curl -X POST "http://localhost:3022/tts" \
  -F "text=Hello, this is text to speech" \
  -F "output_format=wav" \
  -o output.wav
```


## API Endpoints

- `GET /`  
  Root endpoint, provides basic service info.

- `GET /health`  
  Check service health status.

- `GET /compatibility`  
  Check model compatibility.

- `GET /api/models`  
  List available models (models will be downloaded on first request).

- `GET /api/models/{model_name}`  
  Retrieve details of a specific model.

- `POST /api/tts`  
  Convert text into speech (Text-to-Speech).

- `DELETE /cleanup`  
  Clear cache or temporary files.
## Parameters
- `text` - Text to convert to speech
- `model_name` - Model ID (default: xttsv2)
- `output_format` - Audio format (wav, mp3)

## Supported Languages
English (en), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Polish (pl), Turkish (tr), Russian (ru), Dutch (nl), Czech (cs), Arabic (ar), Chinese (zh-cn), Japanese (ja), Hungarian (hu), Korean (ko) Hindi (hi).

Service runs on `http://localhost:3022`
