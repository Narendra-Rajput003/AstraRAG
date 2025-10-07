# config/config.py
# Central configuration: Env vars, constants for scalability.

import os
from dotenv import load_dotenv

load_dotenv()

# Milvus
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "company_docs")

# Gemini
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-pro")

# Paths
UPLOADED_DOCS_DIR = os.getenv("UPLOADED_DOCS_DIR", "data/uploaded_docs")
TEST_DATA_PATH = os.getenv("TEST_DATA_PATH", "data/test_data/test_data.csv")

# Security/Scalability
JWT_SECRET = os.getenv("JWT_SECRET")
POSTGRES_URL = os.getenv("POSTGRES_URL")
REDIS_URL = os.getenv("REDIS_URL")
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", 100))
ALLOWED_ROLES = ["admin", "user"]

# Evaluation
NUM_EVAL_SAMPLES = int(os.getenv("NUM_EVAL_SAMPLES", 10))