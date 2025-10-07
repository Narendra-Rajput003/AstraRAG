import logging
from datetime import datetime,timedelta

from sqlalchemy.sql.functions import user
import jwt
import psycopg2
from redis import Redis 
from config.config import JWT_SECRET, POSTGRES_URL, REDIS_URL, JWT_EXP_MINUTES, REFRESH_EXP_DAYS
from backend.security import hash_password, check_password

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 15  # Short-lived access
REFRESH_EXP_DAYS = 7  # Long-lived refresh


def inititalize_auth_db():
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute(""""
    CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            refresh_token VARCHAR(255)
        )
    """)
    cursor.execute("SELECT * FROM users WHERE username='admin_user'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, role, user_id) VALUES (%s, %s, %s, %s)",
                       ("admin_user", hash_password("admin_pass"), "admin", "admin_123"))
        cursor.execute("INSERT INTO users (username, password_hash, role, user_id) VALUES (%s, %s, %s, %s)",
                       ("employee_user", hash_password("user_pass"), "user", "user_456"))
    conn.commit()
    conn.close()
    logger.info("Auth DB initialized.")

def authenticate_user(username:str,password:str):
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash, role, user_id FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password(password,user[1]):
        return {"username":user[0],"role":user[2],"user_id":user[3]}
    return None

def generate_tokens(user_data:dict) -> tuple:
    access_payload = {
        "username": user_data["username"],
        "role": user_data["role"],
        "user_id":user_data["user_id"],
        "exp":datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }
    
    refresh_payload = {
        "username": user_data["username"],
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXP_DAYS)
    }
    access_token = jwt.encode(access_payload,JWT_SECRET,algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token


def store_refresh_token(username:str,refresh_token:str):
    hashed_refresh = hash_password(refresh_token)
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET refresh_token = %s WHERE username = %s", (hashed_refresh, username))
