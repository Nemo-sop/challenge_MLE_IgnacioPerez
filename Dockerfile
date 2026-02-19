# syntax=docker/dockerfile:1.2
FROM python:3.10-slim

WORKDIR /app

# Configure Python and Uvicorn environments for Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_PORT=8080

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, pre-trained model artifact, and data
COPY challenge/ ./challenge/
COPY data/ ./data/

# Cloud Run expected port
EXPOSE 8080

# Use the optional server runner to enable load adaptation (workers, limits, etc.)
CMD ["python", "-m", "challenge.server"]