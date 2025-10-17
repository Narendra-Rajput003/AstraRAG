import logging
import psycopg2
from datetime import datetime
from config.config import POSTGRES_URL
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def log_audit_event(
    actor_id: Optional[str],
    action: str,
    target: Optional[str] = None,
    meta: Optional[dict] = None,
    ip: Optional[str] = None
):
    """Log audit events to the database."""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO audit_logs (actor_id, action, target, meta, ip)
        VALUES (%s, %s, %s, %s, %s)
        """, (actor_id, action, target, meta, ip))
        conn.commit()
        conn.close()
        logger.info(f"Audit log: {action} by {actor_id}")
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")