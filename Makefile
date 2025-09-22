.PHONY: dev

# Load .env file if exists
ifneq (,$(wildcard .env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif

# Fallback default
HOST ?= 0.0.0.0
PORT ?= 3022

# Python environment setup
install:
	@echo "📦 Installing Python dependencies..."
	python3.11 -m pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

# Local development
run:
	@echo "🚀 Starting TTS API locally..."
	@echo "📍 Loading environment variables from .env file..."
	cd src && python3.11 main.py

dev:
	@echo "🔄 Starting TTS API in development mode with hot reload..."
	@echo "📍 Using HOST=$(HOST), PORT=$(PORT)"
	cd src && python3.11 -m uvicorn main:app --host $(HOST) --port $(PORT) --reload --env-file ../.env
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
	@curl -s http://localhost:3022/health | python3 -m json.tool || echo "❌ API not responding"

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
