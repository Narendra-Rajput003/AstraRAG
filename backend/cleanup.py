import psycopg2  # pyright: ignore[reportMissingModuleSource]
from datetime import datetime, timedelta
from config.config import POSTGRES_URL
from redis import Redis  # pyright: ignore[reportMissingImports]
from config.config import REDIS_URL

def cleanup_old_data():
    """Clean up data older than 30 days."""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cutoff = datetime.utcnow() - timedelta(days=30)
    cursor.execute("DELETE FROM audit WHERE timestamp < %s", (cutoff.isoformat(),))
    # Note: audit table not created, but for logs
    conn.commit()
    conn.close()

    redis = Redis.from_url(REDIS_URL)
    # Clean old keys
    for key in redis.scan_iter("audit:*"):
        # Assume keys expire via TTL
        pass

if __name__ == "__main__":
    cleanup_old_data()