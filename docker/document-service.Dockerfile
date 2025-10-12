FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/rag_pipeline.py ./backend/
COPY config/ ./config/

# Create data directory
RUN mkdir -p /app/data/uploaded_docs

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "backend.document_service:app", "--host", "0.0.0.0", "--port", "8002"]