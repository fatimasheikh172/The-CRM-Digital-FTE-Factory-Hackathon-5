# TechCorp Customer Success AI Agent - Dockerfile
# Multi-purpose image for API and Worker services

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose API port
EXPOSE 8000

# Default command (API server)
# Override in docker-compose or k8s for worker
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
