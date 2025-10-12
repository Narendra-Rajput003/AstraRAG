#!/bin/bash

# AstraRAG Microservices Deployment Script

set -e

echo "🚀 Starting AstraRAG Microservices Deployment"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cat > .env << EOF
# Database Configuration
POSTGRES_USER=astrarag
POSTGRES_PASSWORD=password
JWT_SECRET=$(openssl rand -hex 32)

# MinIO Configuration
MINIO_ACCESS_KEY=astrarag
MINIO_SECRET_KEY=$(openssl rand -hex 32)

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://elasticsearch:9200

# Redis Configuration
REDIS_URL=redis://redis:6379

# Service URLs (for development)
AUTH_SERVICE_URL=http://auth-service:8001
DOCUMENT_SERVICE_URL=http://document-service:8002
SEARCH_SERVICE_URL=http://search-service:8003
ANALYTICS_SERVICE_URL=http://analytics-service:8004
ADMIN_SERVICE_URL=http://admin-service:8005
EOF
    echo "✅ .env file created"
else
    echo "ℹ️  .env file already exists"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/uploaded_docs
mkdir -p docker

# Build and start services
echo "🐳 Building and starting services..."
docker-compose down -v 2>/dev/null || true
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

services=("api-gateway" "auth-service" "document-service" "search-service" "analytics-service" "admin-service")
for service in "${services[@]}"; do
    echo "Checking $service..."
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:${service#*-}/health &>/dev/null; then
            echo "✅ $service is healthy"
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service failed to start properly"
            echo "📋 Checking logs..."
            docker-compose logs $service
            exit 1
        fi

        echo "Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
done

# Run database migrations/initialization
echo "🗄️  Initializing databases..."
docker-compose exec -T postgres psql -U astrarag -d postgres -c "CREATE DATABASE astrarag_auth;" 2>/dev/null || echo "Database astrarag_auth may already exist"
docker-compose exec -T postgres psql -U astrarag -d postgres -c "CREATE DATABASE astrarag_documents;" 2>/dev/null || echo "Database astrarag_documents may already exist"
docker-compose exec -T postgres psql -U astrarag -d postgres -c "CREATE DATABASE astrarag_analytics;" 2>/dev/null || echo "Database astrarag_analytics may already exist"
docker-compose exec -T postgres psql -U astrarag -d postgres -c "CREATE DATABASE astrarag_admin;" 2>/dev/null || echo "Database astrarag_admin may already exist"

# Run tests
echo "🧪 Running tests..."
if docker-compose exec -T api-gateway python -m pytest backend/tests/ -v --tb=short; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed, but deployment continues"
fi

echo ""
echo "🎉 AstraRAG Microservices Deployment Complete!"
echo ""
echo "📋 Service URLs:"
echo "   API Gateway:    http://localhost:8000"
echo "   Auth Service:   http://localhost:8001"
echo "   Document Service: http://localhost:8002"
echo "   Search Service: http://localhost:8003"
echo "   Analytics Service: http://localhost:8004"
echo "   Admin Service:  http://localhost:8005"
echo ""
echo "🔗 Additional Services:"
echo "   MinIO Console:  http://localhost:9001"
echo "   Consul UI:      http://localhost:8500"
echo "   Elasticsearch:  http://localhost:9200"
echo ""
echo "📚 API Documentation: http://localhost:3000/docs"
echo ""
echo "🛑 To stop services: docker-compose down"
echo "🛑 To stop and remove volumes: docker-compose down -v"