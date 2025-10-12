# AstraRAG: Enterprise-Grade RAG System with Microservices Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.11-orange.svg)](https://www.elastic.co/elasticsearch/)

## 🚀 Overview

AstraRAG is a comprehensive, enterprise-grade Retrieval-Augmented Generation (RAG) system built with a modern microservices architecture. It provides secure, scalable document management and intelligent Q&A capabilities powered by Google's Gemini models. The system features advanced search capabilities, real-time collaboration, comprehensive analytics, and robust security measures.

### Key Highlights
- **Microservices Architecture**: 6 specialized services for optimal scalability and maintainability
- **Advanced Search**: Faceted search with Elasticsearch integration and full-text capabilities
- **Real-time Collaboration**: WebSocket-powered document review with live annotations and presence indicators
- **Comprehensive Analytics**: User activity tracking, system metrics, and performance monitoring
- **Enterprise Security**: Multi-factor authentication, security audits, and compliance monitoring
- **Modern Frontend**: React 19 + TypeScript with interactive API documentation
- **Extensive Testing**: 42+ test cases with 80%+ coverage and CI/CD integration

## 🎯 Core Features

### 🔍 Advanced Search & Filtering
- **Full-text Search**: Elasticsearch-powered semantic search with fuzzy matching
- **Faceted Filtering**: Filter by file type, uploader, date range, file size, and custom metadata
- **Pagination & Sorting**: Efficient result navigation with multiple sort options
- **Search Analytics**: Query performance tracking and user behavior insights

### 🤝 Real-time Document Collaboration
- **Live Annotations**: WebSocket-powered comment system with conflict resolution
- **User Presence**: Real-time indicators showing active collaborators
- **Version Tracking**: Document version history with change summaries
- **Shared Reviews**: Multi-user document approval workflows

### 📊 Analytics Dashboard
- **User Activity Metrics**: Login frequency, document interactions, session analytics
- **System Performance**: API response times, error rates, resource utilization
- **Custom Reports**: Exportable analytics in PDF/CSV formats with Chart.js visualizations
- **Real-time Monitoring**: Live metrics via WebSocket integration

### 🏗️ Microservices Architecture
- **API Gateway**: Request routing, authentication, rate limiting, and service discovery
- **Auth Service**: User management, JWT tokens, MFA, and role-based access control
- **Document Service**: File processing, storage (MinIO/S3), and metadata management
- **Search Service**: Elasticsearch integration and advanced query capabilities
- **Analytics Service**: Metrics collection, reporting, and performance monitoring
- **Admin Service**: Administrative operations and security auditing

### 🔒 Enterprise Security
- **Multi-Factor Authentication**: TOTP-based MFA with backup codes for admin users
- **Security Audits**: OWASP Top 10 compliance checks with automated scoring
- **PII Detection**: Presidio-powered sensitive data identification and anonymization
- **Rate Limiting**: Configurable abuse detection with exponential backoff
- **Audit Logging**: Comprehensive activity tracking for compliance

### 📚 API Documentation
- **Interactive Swagger UI**: Complete OpenAPI 3.0.3 specification
- **Live Testing**: Built-in API testing interface with authentication
- **Multi-format Export**: Download OpenAPI specs in JSON format
- **Organized Endpoints**: Grouped by functionality with detailed examples

### 🧪 Testing & Quality Assurance
- **Comprehensive Test Suite**: 42 test cases covering all major functionality
- **80%+ Coverage**: Extensive unit and integration testing
- **Async Testing**: FastAPI endpoint testing with pytest-asyncio
- **CI/CD Ready**: Automated testing pipeline with coverage reporting

## 🛠 Tech Stack

### Backend Services (Microservices)
| Service           | Technologies/Tools                          | Purpose                                      |
|-------------------|---------------------------------------------|----------------------------------------------|
| API Gateway       | FastAPI, httpx, Consul                     | Request routing, service discovery, auth     |
| Auth Service      | FastAPI, PyJWT, Bcrypt, pyotp              | User management, JWT, MFA                    |
| Document Service  | FastAPI, Unstructured, MinIO, Presidio     | Document processing, storage, PII detection  |
| Search Service    | FastAPI, Elasticsearch                      | Advanced search, indexing, faceting          |
| Analytics Service | FastAPI, PostgreSQL, Redis                 | Metrics collection, reporting                |
| Admin Service     | FastAPI, Security audit tools              | Administrative operations, security audits   |

### Frontend & UI
| Component         | Technologies/Tools                          | Purpose                                      |
|-------------------|---------------------------------------------|----------------------------------------------|
| React Application | React 19, TypeScript, Next.js 15            | Modern web application framework             |
| UI Framework      | Tailwind CSS, Framer Motion, Lucide Icons   | Styling, animations, icons                   |
| State Management  | React Context, Custom Hooks                 | Application state and WebSocket integration  |
| API Documentation | Swagger UI, OpenAPI 3.0.3                   | Interactive API documentation                |

### Infrastructure & Data
| Component         | Technologies/Tools                          | Purpose                                      |
|-------------------|---------------------------------------------|----------------------------------------------|
| Databases         | PostgreSQL (multi-schema), Redis            | User data, caching, sessions                 |
| Search Engine     | Elasticsearch 8.11                         | Full-text search, analytics                  |
| Object Storage    | MinIO (S3-compatible)                       | Document storage and retrieval               |
| Service Discovery | Consul 1.15                                | Service registration and health checks       |
| Message Queue     | Redis Pub/Sub                              | Inter-service communication                  |

### Development & Testing
| Component         | Technologies/Tools                          | Purpose                                      |
|-------------------|---------------------------------------------|----------------------------------------------|
| Testing Framework | pytest, pytest-asyncio, pytest-cov          | Unit and integration testing                 |
| Code Quality      | Ruff, ESLint, TypeScript                    | Code linting and type checking               |
| Containerization  | Docker, Docker Compose                      | Service containerization                      |
| CI/CD             | GitHub Actions (implied)                    | Automated testing and deployment             |

### External Integrations
| Service           | Purpose                                      |
|-------------------|----------------------------------------------|
| Google Gemini     | AI-powered question answering and generation |
| Cohere API        | Text reranking and semantic search           |
| WebSocket         | Real-time collaboration features             |

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Docker & Docker Compose**: Latest stable versions
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free space for containers and data
- **Network**: Stable internet connection for external API calls

### API Keys & External Services
- **Google Gemini API Key**: Required for AI-powered Q&A functionality
- **Optional**: Cohere API key for enhanced text reranking
- **Optional**: SMTP service for email notifications (user invites)

### Ports Availability
Ensure these ports are available on your system:
- `8000-8005`: Microservices (API Gateway, Auth, Document, Search, Analytics, Admin)
- `5432`: PostgreSQL database
- `6379`: Redis cache
- `9200`: Elasticsearch
- `8500`: Consul (service discovery)
- `9000-9001`: MinIO (object storage)
- `3000`: Next.js frontend (development)

## 🏗 Installation & Setup

### Quick Start with Docker Compose

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd astrarag
```

2. **Environment Configuration**:
```bash
# The deploy script will create a default .env file
# For production, customize the following variables:
# - JWT_SECRET: Strong random secret for JWT tokens
# - GOOGLE_API_KEY: Your Google Gemini API key
# - MINIO_ACCESS_KEY/MINIO_SECRET_KEY: Object storage credentials
```

3. **Deploy All Services**:
```bash
# Make deploy script executable (Linux/macOS)
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

4. **Access the Application**:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:3000/docs
- **MinIO Console**: http://localhost:9001
- **Consul Dashboard**: http://localhost:8500

### Manual Development Setup

#### Backend Services
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start individual services (in separate terminals)
# API Gateway
python -m uvicorn backend.api_gateway:app --host 0.0.0.0 --port 8000 --reload

# Auth Service
python -m uvicorn backend.auth_service:app --host 0.0.0.0 --port 8001 --reload

# Document Service
python -m uvicorn backend.document_service:app --host 0.0.0.0 --port 8002 --reload

# Search Service
python -m uvicorn backend.search_service:app --host 0.0.0.0 --port 8003 --reload

# Analytics Service
python -m uvicorn backend.analytics_service:app --host 0.0.0.0 --port 8004 --reload

# Admin Service
python -m uvicorn backend.admin_service:app --host 0.0.0.0 --port 8005 --reload
```

#### Frontend Application
```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

### Database Initialization

The system uses separate PostgreSQL databases for each service:
- `astrarag_auth`: User authentication and authorization
- `astrarag_documents`: Document metadata and processing status
- `astrarag_analytics`: User activity and system metrics
- `astrarag_admin`: Administrative operations and audit logs

Databases are automatically created and initialized when using Docker Compose.

### Testing

```bash
# Run all tests
pytest backend/tests/ -v --cov=backend --cov-report=html

# Run specific service tests
pytest backend/tests/test_auth.py -v
pytest backend/tests/test_api.py -v

# Generate coverage report
open htmlcov/index.html
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Security
JWT_SECRET=your-super-secret-jwt-key-here
JWT_EXP_MINUTES=30
REFRESH_EXP_DAYS=7

# Database
POSTGRES_USER=astrarag
POSTGRES_PASSWORD=password

# Redis
REDIS_URL=redis://redis:6379

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_INDEX=documents

# MinIO Object Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=astrarag
MINIO_SECRET_KEY=astrarag-secret

# External APIs
GOOGLE_API_KEY=your-gemini-api-key
COHERE_API_KEY=your-cohere-api-key

# Service URLs (for development)
AUTH_SERVICE_URL=http://auth-service:8001
DOCUMENT_SERVICE_URL=http://document-service:8002
SEARCH_SERVICE_URL=http://search-service:8003
ANALYTICS_SERVICE_URL=http://analytics-service:8004
ADMIN_SERVICE_URL=http://admin-service:8005
```

### Service Discovery

Consul automatically handles service registration and discovery. Services register themselves on startup and are automatically load-balanced by the API Gateway.

### Troubleshooting

#### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check what's using specific ports
   netstat -tulpn | grep :8000
   # Stop conflicting services or change ports in docker-compose.yml
   ```

2. **Elasticsearch Connection Issues**:
   ```bash
   # Check Elasticsearch health
   curl http://localhost:9200/_cluster/health
   # View Elasticsearch logs
   docker-compose logs elasticsearch
   ```

3. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL status
   docker-compose ps postgres
   # View database logs
   docker-compose logs postgres
   ```

4. **MinIO/S3 Issues**:
   ```bash
   # Access MinIO console
   open http://localhost:9001
   # Default credentials: astrarag / astrarag-secret
   ```

5. **Service Health Checks**:
   ```bash
   # Check all service health
   curl http://localhost:8000/health

   # Check individual services
   for port in {8001..8005}; do
     curl -f http://localhost:$port/health || echo "Service on port $port unhealthy"
   done
   ```

#### Memory Issues
- **Increase Docker memory limit** to at least 8GB
- **Monitor resource usage**: `docker stats`
- **Scale down services** if needed during development

#### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-gateway
docker-compose logs -f elasticsearch

# Restart specific service
docker-compose restart api-gateway

# Rebuild and restart service
docker-compose up -d --build api-gateway
```

## 💬 Usage Guide

### Getting Started

1. **Deploy the System**:
  ```bash
  ./deploy.sh
  ```

2. **Access the Application**:
  - Open http://localhost:3000 in your browser
  - Default admin credentials will be displayed in the deployment logs

3. **First-Time Setup**:
  - Complete admin user registration
  - Configure system settings through the admin panel
  - Upload initial documents for testing

### User Workflow

#### For End Users
1. **Login**: Access the application with your credentials
2. **Search Documents**: Use the advanced search interface with filters
3. **Ask Questions**: Query the knowledge base using natural language
4. **Collaborate**: Join document review sessions with live annotations

#### For Administrators
1. **User Management**: Create invites and manage user roles
2. **Document Oversight**: Upload documents and manage approval workflows
3. **Security Monitoring**: Run security audits and review system health
4. **Analytics Review**: Monitor user activity and system performance

### API Usage

#### Authentication Flow
```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
 -H "Content-Type: application/json" \
 -d '{"email": "admin@example.com", "password": "password"}'

# 2. Use returned access_token for authenticated requests
curl -X GET http://localhost:8000/search/documents \
 -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Document Upload
```bash
# Upload a PDF document
curl -X POST http://localhost:8000/policies/upload \
 -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
 -F "file=@document.pdf"
```

#### Advanced Search
```bash
# Search with filters
curl -X POST http://localhost:8000/search/documents \
 -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
 -H "Content-Type: application/json" \
 -d '{
   "query": "company policy",
   "filters": {
     "file_type": "pdf",
     "uploaded_by": "admin@example.com"
   },
   "sort_by": "uploaded_at",
   "page": 1,
   "size": 20
 }'
```

## 🧠 Architecture Overview

### Microservices Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Web Browser   │  │   Mobile App    │  │   API Client │  │
│  │   (React SPA)   │  │   (React Native)│  │   (Postman)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 API Gateway Service (Port 8000)             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ • Request Routing & Load Balancing                 │    │
│  │ • Authentication & Authorization                   │    │
│  │ • Rate Limiting & Abuse Detection                  │    │
│  │ • Request/Response Transformation                  │    │
│  │ • Service Discovery Integration                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Auth Service │ │ Doc Service │ │Search Service│
│ (Port 8001)  │ │ (Port 8002)  │ │ (Port 8003)  │
│             │ │             │ │             │
│ • User Mgmt  │ │ • Doc Upload │ │ • ES Search │
│ • JWT/MFA    │ │ • Processing │ │ • Indexing  │
│ • RBAC       │ │ • MinIO/S3   │ │ • Faceting  │
└─────────────┘ └─────────────┘ └─────────────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
                     ▼
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Analytics Svc│ │ Admin Service│ │Consul       │
│ (Port 8004)  │ │ (Port 8005)  │ │(Discovery)  │
│             │ │             │ │             │
│ • Metrics    │ │ • Security   │ │ • Service   │
│ • Reporting  │ │ • Audit      │ │ • Health    │
│ • Dashboards │ │ • User Mgmt  │ │ • Config    │
└─────────────┘ └─────────────┘ └─────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │ PostgreSQL  │ │   Redis     │ │ Elasticsearch│ │  MinIO  │ │
│  │ (Multi-DB)  │ │ (Cache)     │ │ (Search)     │ │ (S3)    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Service Communication Patterns

- **API Gateway → Microservices**: HTTP/JSON with service discovery
- **Inter-service Communication**: Direct HTTP calls with circuit breakers
- **Real-time Features**: WebSocket connections through API Gateway
- **Event Streaming**: Redis Pub/Sub for cross-service events
- **Service Discovery**: Consul for automatic service registration

### Data Flow Architecture

```
User Request → API Gateway → Authentication → Target Service → Database/Storage
      ↓              ↓              ↓              ↓              ↓
  Response ← Load Balancer ← Service Discovery ← Business Logic ← Data Access
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Security Layers                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ API Gateway: Rate Limiting, Auth, Input Validation │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Service Layer: Business Logic Validation           │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Data Layer: PII Detection, Access Control          │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Infrastructure: Network Security, Encryption       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## ☁️ Deployment Options

### Local Development
```bash
# Quick deployment with all services
./deploy.sh

# Manual service management
docker-compose up -d              # Start all services
docker-compose logs -f            # View logs
docker-compose down               # Stop all services
docker-compose down -v            # Stop and remove volumes
```

### Production Deployment

#### Docker Compose (Recommended for Small-Scale)
```bash
# Production configuration
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
cp .env.example .env.prod
docker-compose --env-file .env.prod up -d
```

#### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/api-gateway
```

#### Cloud Platforms

**AWS**:
```bash
# ECS/Fargate deployment
aws ecs create-cluster --cluster-name astrarag
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json

# RDS for PostgreSQL, ElastiCache for Redis, Elasticsearch Service
```

**Google Cloud**:
```bash
# GKE deployment
gcloud container clusters create astrarag-cluster
kubectl apply -f k8s/

# Cloud SQL, Memorystore, Vertex AI integration
```

**Azure**:
```bash
# AKS deployment
az aks create --resource-group astrarag --name astrarag-cluster
kubectl apply -f k8s/

# Azure Database, Cache, Cognitive Search integration
```

### High Availability Setup

```yaml
# Example: Multi-zone deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - api-gateway
              topologyKey: kubernetes.io/zone
```

## 🔗 API Integrations

### Google Gemini Integration
- **Purpose**: AI-powered question answering and document analysis
- **Configuration**: Set `GOOGLE_API_KEY` in environment variables
- **Features**:
  - Natural language query processing
  - Document content summarization
  - Contextual answer generation
  - Multi-modal content analysis

### Cohere API Integration (Optional)
- **Purpose**: Enhanced text reranking and semantic search
- **Configuration**: Set `COHERE_API_KEY` for improved search relevance
- **Features**:
  - Query-result relevance scoring
  - Semantic similarity ranking
  - Multi-language support

### WebSocket Integration
- **Purpose**: Real-time collaboration and live updates
- **Configuration**: Automatic setup with Socket.IO
- **Features**:
  - Live document annotations
  - User presence indicators
  - Real-time notifications
  - Collaborative editing support

### Elasticsearch Integration
- **Purpose**: Advanced full-text search and analytics
- **Configuration**: Automatic index creation and management
- **Features**:
  - Fuzzy search and autocomplete
  - Faceted filtering
  - Search analytics and reporting
  - Real-time indexing

### MinIO/S3 Integration
- **Purpose**: Scalable document storage
- **Configuration**: S3-compatible object storage
- **Features**:
  - Automatic file versioning
  - CDN integration ready
  - Cross-region replication
  - Lifecycle management

## 📊 Monitoring & Analytics

### System Metrics
- **API Response Times**: Track performance bottlenecks
- **Error Rates**: Monitor service health and reliability
- **Resource Utilization**: CPU, memory, and disk usage
- **User Activity**: Login frequency and feature usage

### Logging & Alerting
- **Centralized Logging**: ELK stack integration ready
- **Alert Management**: Configurable thresholds and notifications
- **Audit Trails**: Comprehensive activity logging
- **Performance Monitoring**: Real-time metrics dashboard

### Health Checks
```bash
# Service health endpoints
GET /health          # Overall system health
GET /metrics         # Prometheus metrics
GET /ready           # Readiness probe
GET /live           # Liveness probe
```

## 💰 Cost Estimation

### Infrastructure Costs (Monthly)

| Service | Development | Production (Small) | Production (Large) |
|---------|-------------|-------------------|-------------------|
| **Compute** | $50-100 | $200-500 | $1000-3000 |
| **Databases** | $20-50 | $100-300 | $500-2000 |
| **Storage** | $5-20 | $50-200 | $200-1000 |
| **Search** | $20-50 | $100-300 | $500-1500 |
| **CDN** | $0-10 | $50-200 | $200-1000 |
| **Monitoring** | $10-30 | $50-150 | $200-500 |
| **Total** | **$105-260** | **$550-1650** | **$2600-9000** |

### API Costs (Per 1M requests)

| Service | Cost | Notes |
|---------|------|-------|
| **Google Gemini** | $0.01-0.05 | Per query, depends on model |
| **Cohere** | $0.005-0.02 | Optional, for reranking |
| **Elasticsearch** | $0.10-0.50 | Per GB stored/searched |
| **MinIO/S3** | $0.02-0.05 | Per GB stored/transferred |

### Optimization Strategies
- **Caching**: Redis reduces API calls by 60-80%
- **CDN**: Global content delivery reduces latency
- **Auto-scaling**: Pay only for actual usage
- **Reserved Instances**: 30-50% savings for predictable workloads

## 🤝 Contributing

We welcome contributions to AstraRAG! Here's how you can help:

### Development Workflow

1. **Fork the Repository**:
   ```bash
   git clone https://github.com/your-org/astrarag.git
   cd astrarag
   git checkout -b feature/your-feature-name
   ```

2. **Set Up Development Environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   cd frontend && npm install

   # Start development services
   docker-compose -f docker-compose.dev.yml up -d

   # Run tests
   pytest backend/tests/ -v
   ```

3. **Code Standards**:
   - **Backend**: Follow PEP8, use type hints, write comprehensive tests
   - **Frontend**: Use TypeScript, follow React best practices
   - **Documentation**: Update README and docstrings for new features
   - **Security**: Run security audits before submitting changes

4. **Testing Requirements**:
   ```bash
   # Run full test suite
   pytest backend/tests/ --cov=backend --cov-report=html

   # Frontend testing
   cd frontend && npm test

   # Integration tests
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit
   ```

5. **Submit Changes**:
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   git push origin feature/your-feature-name
   # Create Pull Request
   ```

### Architecture Guidelines

- **Microservices**: Keep services focused on single responsibilities
- **API Design**: RESTful APIs with OpenAPI documentation
- **Security**: Implement authentication and authorization properly
- **Testing**: 80%+ code coverage, integration tests for APIs
- **Documentation**: Update README and create API docs for new endpoints

### Service-Specific Guidelines

#### Adding New Microservices
1. Create service directory structure
2. Implement health checks and metrics
3. Add service to Docker Compose
4. Update API Gateway routing
5. Add comprehensive tests

#### Database Changes
1. Use migrations for schema changes
2. Update all relevant service schemas
3. Test backward compatibility
4. Document breaking changes

## 📋 API Reference

### Core Endpoints

#### Authentication
```
POST /auth/login              # User login
POST /auth/register           # User registration
POST /auth/mfa/setup          # Setup MFA
POST /auth/mfa/verify         # Verify MFA
GET  /auth/validate           # Validate token
```

#### Document Management
```
POST /policies/upload         # Upload document
GET  /documents               # List documents
GET  /documents/{id}          # Get document details
POST /admin/documents/approve # Approve/reject document
```

#### Search & Analytics
```
POST /search/documents        # Advanced search
GET  /search/facets           # Get search facets
GET  /analytics/user-activity # User analytics
GET  /analytics/system-metrics # System metrics
```

#### Administration
```
GET  /admin/users             # List users
PUT  /admin/users/{id}/status # Update user status
GET  /admin/security-audit    # Run security audit
GET  /admin/audit-logs        # Get audit logs
```

### Response Formats

#### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed"
}
```

#### Error Response
```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": { ... }
}
```

### Authentication Headers
```
Authorization: Bearer <jwt_token>
X-API-Key: <service_api_key>
X-User-ID: <user_id>          # Set by API Gateway
X-User-Role: <user_role>      # Set by API Gateway
```

## 🔧 Advanced Configuration

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | Required | JWT signing secret |
| `POSTGRES_URL` | Required | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | Elasticsearch endpoint |
| `GOOGLE_API_KEY` | Required | Google Gemini API key |
| `MINIO_ACCESS_KEY` | `astrarag` | MinIO access key |
| `MINIO_SECRET_KEY` | `astrarag-secret` | MinIO secret key |

### Service Discovery Configuration

Services automatically register with Consul. Configuration:

```json
{
  "service": {
    "name": "api-gateway",
    "port": 8000,
    "check": {
      "http": "http://localhost:8000/health",
      "interval": "30s",
      "timeout": "5s"
    }
  }
}
```

### Monitoring Setup

#### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'astrarag-services'
    static_configs:
      - targets: ['api-gateway:8000', 'auth-service:8001', 'document-service:8002']
    metrics_path: '/metrics'
```

#### Grafana Dashboards
Pre-built dashboards available in `monitoring/grafana/` directory.

## 🆘 Support & Community

### Getting Help

1. **Documentation**: Check this README and API docs first
2. **GitHub Issues**: Search existing issues or create new ones
3. **Community Forum**: Join our Discord community
4. **Professional Support**: Contact enterprise@astrarag.com

### Issue Reporting

When reporting bugs, please include:
- AstraRAG version and commit hash
- Docker Compose version
- Full error logs and stack traces
- Steps to reproduce the issue
- System information (OS, memory, etc.)

### Feature Requests

We welcome feature requests! Please:
- Check if the feature already exists
- Describe the use case and benefits
- Provide mockups or examples if applicable
- Consider backward compatibility

## 📄 License

AstraRAG is licensed under the MIT License. See [LICENSE](LICENSE) for full terms.

### Third-Party Licenses

This project includes third-party components:
- **FastAPI**: MIT License
- **React**: MIT License
- **Elasticsearch**: Apache 2.0
- **PostgreSQL**: PostgreSQL License
- **Redis**: BSD License

## 🙏 Acknowledgments

- **Google**: For the Gemini AI platform
- **Elastic**: For Elasticsearch
- **FastAPI**: For the excellent web framework
- **React**: For the frontend framework
- **Open Source Community**: For the countless libraries and tools

---

**Built with ❤️ for the enterprise AI community**
