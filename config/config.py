# config/config.py
# Central configuration: Env vars, constants for scalability.

import os
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv()

# Milvus
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "company_docs")

# Gemini
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# Paths
UPLOADED_DOCS_DIR = os.getenv("UPLOADED_DOCS_DIR", "data/uploaded_docs")
TEST_DATA_PATH = os.getenv("TEST_DATA_PATH", "data/test_data/test_data.csv")

# Security/Scalability
JWT_SECRET = os.getenv("JWT_SECRET")
POSTGRES_URL = os.getenv("POSTGRES_URL")
REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = os.getenv("REDIS_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "documents")
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", 100))
ALLOWED_ROLES = ["admin", "user", "employee", "admin:hr", "superadmin"]
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", 30))
REFRESH_EXP_DAYS = int(os.getenv("REFRESH_EXP_DAYS", 7))

# Evaluation
NUM_EVAL_SAMPLES = int(os.getenv("NUM_EVAL_SAMPLES", 10))