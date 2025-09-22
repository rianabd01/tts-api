# Use Python 3.11 slim image for better compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

COPY . .

WORKDIR /app/src

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV TORCH_DISABLE_WEIGHTS_ONLY=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies + Rust
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    pkg-config \
    # Audio processing dependencies
    ffmpeg \
    libsndfile1-dev \
    libffi-dev \
    libasound2-dev \
    portaudio19-dev \
    # Rust compiler (buat sudachipy)
    rustc \
    cargo \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch first with specific version for stability
RUN pip install --no-cache-dir torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with error handling for problematic packages
RUN pip install --no-cache-dir fastapi==0.104.1 && \
    pip install --no-cache-dir uvicorn[standard]==0.24.0 && \
    pip install --no-cache-dir python-multipart==0.0.6 && \
    pip install --no-cache-dir pydantic==2.5.0 && \
    pip install --no-cache-dir pydantic-settings==2.1.0 && \
    pip install --no-cache-dir aiofiles==23.2.1 && \
    pip install --no-cache-dir requests && \
    pip install --no-cache-dir numpy && \
    pip install --no-cache-dir scipy && \
    pip install --no-cache-dir soundfile && \
    pip install --no-cache-dir librosa

# Install Coqui TTS (may take time and has many dependencies)
RUN pip install --no-cache-dir coqui-tts==0.24.2

# Copy application files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p ./cache ./outputs && \
    chmod 755 ./cache ./outputs

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3022

# Health check (extended timeout for model loading)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:3022/health || exit 1

ENV COQUI_TOS_AGREED=1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3022", "--workers", "1"]