# AstraRAG Microservices Architecture

This document describes the microservices architecture implementation for AstraRAG, a comprehensive document management and RAG (Retrieval-Augmented Generation) system.

## Architecture Overview

The application has been refactored from a monolithic architecture into a distributed microservices system with the following components:

### Services

1. **API Gateway** (Port 8000)
   - Entry point for all client requests
   - Request routing and load balancing
   - Authentication middleware
   - Rate limiting
   - Service discovery integration

2. **Authentication Service** (Port 8001)
   - User authentication and authorization
   - JWT token management
   - MFA (Multi-Factor Authentication)
   - User registration and invites
   - Session management

3. **Document Service** (Port 8002)
   - Document upload and processing
   - File storage (MinIO/S3)
   - Text extraction and PII anonymization
   - Document metadata management
   - Document approval workflow

4. **Search Service** (Port 8003)
   - Elasticsearch integration
   - Advanced document search with faceting
   - Document indexing and updates
   - Search analytics and metrics

5. **Analytics Service** (Port 8004)
   - User activity tracking
   - System performance metrics
   - Dashboard data aggregation
   - Event logging and reporting

6. **Admin Service** (Port 8005)
   - Administrative operations
   - Security audit functionality
   - User management
   - System monitoring and logs

### Infrastructure

- **PostgreSQL**: Primary database with separate schemas for each service
- **Redis**: Caching and session storage
- **Elasticsearch**: Document search and indexing
- **MinIO**: Object storage for documents
- **Consul**: Service discovery and health checking

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 8GB RAM recommended
- Ports 8000-8005, 5432, 6379, 9200, 8500, 9000-9001 available

### Environment Setup

1. Create environment file:
```bash
cp .env.example .env
```

2. Configure the following variables in `.env`:
```env
# Database
POSTGRES_USER=astrarag
POSTGRES_PASSWORD=password
JWT_SECRET=your-super-secret-jwt-key-here

# MinIO Storage
MINIO_ACCESS_KEY=astrarag
MINIO_SECRET_KEY=astrarag-secret

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200
```

### Deployment

1. Start all services:
```bash
docker-compose up -d
```

2. Check service health:
```bash
# Check all services
curl http://localhost:8000/health

# Check individual services
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

3. Access the application:
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Documentation: http://localhost:3000/docs

### Service URLs

- API Gateway: http://localhost:8000
- Auth Service: http://localhost:8001
- Document Service: http://localhost:8002
- Search Service: http://localhost:8003
- Analytics Service: http://localhost:8004
- Admin Service: http://localhost:8005

## Development

### Running Individual Services

Each service can be run independently for development:

```bash
# Auth Service
cd backend && python -m uvicorn auth_service:app --host 0.0.0.0 --port 8001 --reload

# Document Service
cd backend && python -m uvicorn document_service:app --host 0.0.0.0 --port 8002 --reload

# Search Service
cd backend && python -m uvicorn search_service:app --host 0.0.0.0 --port 8003 --reload

# Analytics Service
cd backend && python -m uvicorn analytics_service:app --host 0.0.0.0 --port 8004 --reload

# Admin Service
cd backend && python -m uvicorn admin_service:app --host 0.0.0.0 --port 8005 --reload

# API Gateway
cd backend && python -m uvicorn api_gateway:app --host 0.0.0.0 --port 8000 --reload
```

### Testing

Run tests for individual services:

```bash
# Run all tests
pytest backend/tests/

# Run specific service tests
pytest backend/tests/test_auth.py -v
pytest backend/tests/test_api.py -v
```

### Database Migrations

Each service has its own database schema. To update schemas:

1. Connect to the appropriate database
2. Run migration scripts in `docker/init-db.sql`

## API Documentation

### Authentication Flow

1. **Login**: `POST /auth/login`
   - Returns JWT tokens and MFA requirement status
   - If MFA required, returns temporary token

2. **MFA Verification**: `POST /auth/mfa/authenticate`
   - Verify MFA code for login completion

3. **Token Validation**: `GET /auth/validate`
   - Validate JWT tokens on each request

### Document Management

1. **Upload Document**: `POST /policies/upload`
   - Accepts PDF files up to 10MB
   - Automatic text extraction and PII detection
   - Queues for admin approval

2. **Search Documents**: `POST /search/documents`
   - Advanced search with filters and faceting
   - Pagination support
   - Full-text search with Elasticsearch

3. **Admin Approval**: `POST /admin/documents/approve`
   - Approve or reject pending documents
   - Updates search index automatically

### Analytics

1. **User Activity**: `GET /analytics/user-activity`
   - Login frequency, document interactions
   - Daily activity breakdowns

2. **System Metrics**: `GET /analytics/system-metrics`
   - API response times, error rates
   - Database and cache performance

### Security Audit

1. **Run Audit**: `GET /admin/security-audit`
   - Comprehensive security assessment
   - OWASP Top 10 compliance checks

2. **Audit Summary**: `GET /admin/security-audit/summary`
   - Quick overview for regular admins

## Monitoring and Logging

### Health Checks

All services expose health check endpoints:
- `GET /health` - Service health status
- Includes database and dependency connectivity

### Metrics

- **Prometheus**: System metrics collection
- **Grafana**: Metrics visualization dashboards
- **ELK Stack**: Centralized logging (optional)

### Service Discovery

- **Consul**: Automatic service registration and discovery
- Health checking and load balancing
- Configuration management

## Security Features

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- Session management and timeout

### Data Protection
- PII detection and anonymization
- Encrypted data storage
- Secure file upload validation
- Rate limiting and abuse detection

### Security Auditing
- Comprehensive security assessments
- Real-time monitoring and alerts
- Audit logging for all administrative actions
- Compliance reporting

## Scaling and Performance

### Horizontal Scaling
- Stateless services enable easy scaling
- Load balancing through API Gateway
- Database connection pooling
- Redis clustering for caching

### Caching Strategy
- Redis for session and application data
- Browser caching for static assets
- CDN integration for global content delivery

### Database Optimization
- Separate databases per service
- Proper indexing on key fields
- Query optimization and profiling
- Connection pooling

## Troubleshooting

### Common Issues

1. **Service Unavailable**
   - Check service health: `docker-compose ps`
   - View logs: `docker-compose logs <service-name>`
   - Verify network connectivity

2. **Database Connection Issues**
   - Ensure PostgreSQL is running: `docker-compose logs postgres`
   - Check connection strings in environment variables
   - Verify database initialization

3. **Elasticsearch Issues**
   - Check cluster health: `curl http://localhost:9200/_cluster/health`
   - Verify index creation and mappings
   - Check disk space and memory usage

4. **MinIO/S3 Issues**
   - Access MinIO console: http://localhost:9001
   - Verify credentials and bucket creation
   - Check storage permissions

### Logs and Debugging

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-gateway

# Check service discovery
curl http://localhost:8500/v1/catalog/services

# Database debugging
docker-compose exec postgres psql -U astrarag -d astrarag
```

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update API documentation
4. Ensure all services remain stateless
5. Test inter-service communication
6. Update this README for any architectural changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.