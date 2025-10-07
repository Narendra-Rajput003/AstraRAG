# AstraRAG: Scalable Retrieval-Augmented Generation Q&A Chatbot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-orange.svg)](https://streamlit.io/)

## 🚀 Overview
AstraRAG is a production-ready, enterprise-grade Retrieval-Augmented Generation (RAG) chatbot designed for secure, scalable knowledge management in organizations. It supports large document ingestion (PDFs, tables, images), semantic searches, and grounded responses using Google's Gemini models. Role-based access control (RBAC), PII anonymization, and vector filtering ensure privacy and compliance.

## 🎯 Features
- Advanced RAG Pipeline: Semantic chunking, multi-query retrieval, Cohere reranking, iterative refinement.
- Scalability: Milvus vector storage, async ingestion, Redis caching, Docker/K8s-ready.
- Security & Compliance: JWT auth, RBAC, PII masking with Presidio, dynamic filters.
- Evaluation & Monitoring: Ragas metrics (faithfulness, relevancy), Prometheus integration.
- User-Friendly UI: Streamlit chat with history, role-specific views, admin uploads.
- Extensibility: Modular LangChain backend, multimodal document support.

## 🛠 Tech Stack
| Category          | Technologies/Tools                          | Purpose                                      |
|-------------------|---------------------------------------------|----------------------------------------------|
| Core Framework    | LangChain, Google Gemini (1.5 Pro/Flash)   | RAG pipeline, embeddings, generation        |
| Vector DB         | Milvus (pymilvus)                          | Scalable similarity search and filtering    |
| Auth/Security     | PyJWT, Bcrypt, Presidio, Redis              | Auth, rate limiting, PII anonymization      |
| Database          | PostgreSQL (psycopg2)                      | User storage with RBAC metadata             |
| Caching/Monitoring| Redis, Prometheus                           | Rate limiting, caching, metrics             |
| Frontend/UI       | Streamlit, streamlit-chat                  | Interactive chat interface                  |
| Document Parsing  | Unstructured, SemanticChunker               | Large document parsing                       |
| Evaluation        | Ragas, Datasets, Pandas                     | QA performance measurement                   |
| Deployment        | Docker Compose, Dockerfile, K8s             | Containerized setup                           |
| Other             | Cohere (reranking), asyncio, pickle         | Async ops, serialization                     |

## 📋 Prerequisites
- Python 3.10+
- Docker & Docker Compose
- API Keys: Google Gemini, Cohere
- Minimum 8GB RAM (GPU optional for Milvus)

## 🏗 Installation & Setup
```bash
# 1. Clone Repository
git clone <your-repo-url> AstraRAG
cd AstraRAG
cp .env.example .env
# Edit .env with API keys, DB, and Redis URLs

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Run with Docker Compose
docker-compose up --build
# App: http://localhost:8501
# Prometheus: http://localhost:9090

# 4. Local Manual Setup (Optional)
docker run -p 19530:19530 -p 2379:2379 milvusdb/milvus:latest
docker run -p 5432:5432 -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin postgres:latest
docker run -p 6379:6379 redis:latest
streamlit run src/frontend/app.py

5. Database Initialization
Admin: admin_user / admin_pass
Employee: employee_user / user_pass

💬 Usage
- Login with credentials (Admin/User)
- Admin uploads documents → auto-indexed in Milvus
- Users query via chat → grounded answers
- Admin evaluates RAG metrics via sidebar
- Monitor with Prometheus dashboard

🧠 Architecture Overview
┌─────────────────┐   ┌─────────────────┐
│   Streamlit UI  │───│   JWT Auth/RBAC │
└─────────────────┘   └─────────────────┘
         │                     │
         ▼                     ▼
┌───────────────────────────┐  ┌──────────────────────┐
│ RAG Pipeline (LangChain)  │  │ PII Masking (Presidio) │
└───────────────────────────┘  └──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Milvus (Vector DB)   │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ PostgreSQL (Users)   │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Redis (Cache/Limits) │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Prometheus (Metrics) │
└──────────────────────┘

☁️ Deployment
Local: docker-compose up
Production (K8s/Cloud): Build & push Docker image, deploy manifests, enable HTTPS, integrate Grafana/Prometheus

💰 Cost Estimate
Milvus: $50–200/month
Gemini API: $0.01–0.05/query
PostgreSQL/Redis: $20–100/month

🤝 Contributing
- Fork repo
- Create feature branch: git checkout -b feature/amazing-feature
- Commit: git commit -m 'Add amazing feature'
- Push: git push origin feature/amazing-feature
- Open PR
Guidelines: Follow PEP8, write pytest tests, update README

📄 License
MIT License — see LICENSE

🆘 Support
- Issues: GitHub Issues
- Email: contact@astrarag.com
- Discord: Community support
