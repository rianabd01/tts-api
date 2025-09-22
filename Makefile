# TTS API Makefile
# Makes it easy to manage the Coqui TTS application

.PHONY: help install run docker-build docker-run docker-arm64 docker-arm64-safe docker-minimal stop clean test health logs env env-local env-docker env-arm64 env-show env-reset

# Python environment setup
install:
	@echo "📦 Installing Python dependencies..."
	pip3 install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

# Local development
run:
	@echo "🚀 Starting TTS API locally..."
	cd src && python3 main.py

dev:
	@echo "🔄 Starting TTS API in development mode..."
	cd src && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Docker commands
docker-build:
	@echo "🔨 Building Docker image for x86_64..."
	docker-compose build

	@echo "🚀 Building minimal ARM64 Docker image (fastest & most compatible)..."
	DOCKERFILE=Dockerfile.arm64.minimal docker-compose up --build

docker-run:
	@echo "🐳 Starting TTS API with Docker..."
	docker-compose up --build

docker-logs:
	@echo "📋 Viewing Docker container logs..."
	docker-compose logs -f coqui-tts-api

# Health and monitoring
health:
	@echo "🏥 Checking TTS API health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ API not responding"

# Architecture detection and smart start
start:
	@echo "🎙️ Starting TTS API (auto-detecting architecture)..."
	@if [ "$$(uname -m)" = "arm64" ] || [ "$$(uname -m)" = "aarch64" ]; then \
		echo "🍎 Detected ARM64 - using optimized startup..."; \
		./start-arm64.sh; \
	else \
		echo "💻 Detected x86_64 - using standard startup..."; \
		./start.sh; \
	fi
