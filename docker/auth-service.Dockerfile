FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/auth.py ./backend/
COPY backend/audit.py ./backend/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "backend.auth_service:app", "--host", "0.0.0.0", "--port", "8001"]