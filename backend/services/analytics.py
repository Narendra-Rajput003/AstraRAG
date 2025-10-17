import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from config.config import POSTGRES_URL

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.db_url = POSTGRES_URL

    def track_event(self, user_id: str, event_type: str, event_data: Dict[str, Any] = None,
                   session_id: str = None, ip_address: str = None, user_agent: str = None):
        """Track a user analytics event."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO analytics_events (user_id, event_type, event_data, session_id, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, event_type, event_data or {}, session_id, ip_address, user_agent))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")

    def get_user_activity_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user activity metrics."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Calculate date range
            start_date = datetime.now() - timedelta(days=days)

            # User login frequency
            cursor.execute("""
            SELECT
                DATE(last_login) as login_date,
                COUNT(*) as login_count
            FROM users
            WHERE last_login >= %s
            GROUP BY DATE(last_login)
            ORDER BY login_date
            """, (start_date,))

            login_data = cursor.fetchall()

            # Document upload activity
            cursor.execute("""
            SELECT
                DATE(uploaded_at) as upload_date,
                COUNT(*) as upload_count,
                SUM(metadata->>'file_size')::bigint as total_size
            FROM documents
            WHERE uploaded_at >= %s AND status = 'active'
            GROUP BY DATE(uploaded_at)
            ORDER BY upload_date
            """, (start_date,))

            upload_data = cursor.fetchall()

            # QA session activity
            cursor.execute("""
            SELECT
                DATE(timestamp) as session_date,
                COUNT(*) as session_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM qa_sessions
            WHERE timestamp >= %s
            GROUP BY DATE(timestamp)
            ORDER BY session_date
            """, (start_date,))

            qa_data = cursor.fetchall()

            # Search activity
            cursor.execute("""
            SELECT
                DATE(created_at) as search_date,
                COUNT(*) as search_count
            FROM analytics_events
            WHERE event_type = 'search_performed' AND created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY search_date
            """, (start_date,))

            search_data = cursor.fetchall()

            # User engagement metrics
            cursor.execute("""
            SELECT
                COUNT(DISTINCT user_id) as total_users,
                COUNT(DISTINCT CASE WHEN last_login >= %s THEN user_id END) as active_users,
                AVG(EXTRACT(EPOCH FROM (last_login - created_at))/86400) as avg_user_age_days
            FROM users
            WHERE is_active = true
            """, (start_date,))

            user_metrics = cursor.fetchone()

            conn.close()

            return {
                "login_activity": [
                    {"date": str(row[0]), "logins": row[1]}
                    for row in login_data
                ],
                "upload_activity": [
                    {"date": str(row[0]), "uploads": row[1], "total_size": row[2] or 0}
                    for row in upload_data
                ],
                "qa_activity": [
                    {"date": str(row[0]), "sessions": row[1], "unique_users": row[2]}
                    for row in qa_data
                ],
                "search_activity": [
                    {"date": str(row[0]), "searches": row[1]}
                    for row in search_data
                ],
                "user_metrics": {
                    "total_users": user_metrics[0] or 0,
                    "active_users": user_metrics[1] or 0,
                    "avg_user_age_days": round(user_metrics[2] or 0, 1)
                },
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Failed to get user activity metrics: {e}")
            return {}

    def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            start_time = datetime.now() - timedelta(hours=hours)

            # API response times
            cursor.execute("""
            SELECT
                metric_type,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as sample_count
            FROM system_metrics
            WHERE metric_type LIKE 'api_response_time_%'
                AND recorded_at >= %s
            GROUP BY metric_type
            """, (start_time,))

            api_metrics = cursor.fetchall()

            # Error rates
            cursor.execute("""
            SELECT
                DATE(recorded_at) as error_date,
                COUNT(*) as error_count
            FROM system_metrics
            WHERE metric_type = 'api_error'
                AND recorded_at >= %s
            GROUP BY DATE(recorded_at)
            ORDER BY error_date
            """, (start_time,))

            error_data = cursor.fetchall()

            # Database connection pool metrics
            cursor.execute("""
            SELECT
                metric_type,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value
            FROM system_metrics
            WHERE metric_type LIKE 'db_connection_%'
                AND recorded_at >= %s
            GROUP BY metric_type
            """, (start_time,))

            db_metrics = cursor.fetchall()

            # Storage metrics
            cursor.execute("""
            SELECT
                SUM((metadata->>'file_size')::bigint) as total_storage,
                COUNT(*) as total_files,
                AVG((metadata->>'file_size')::bigint) as avg_file_size
            FROM documents
            WHERE status = 'active'
            """)

            storage_metrics = cursor.fetchone()

            conn.close()

            return {
                "api_performance": [
                    {
                        "endpoint": row[0].replace('api_response_time_', ''),
                        "avg_response_time": round(row[1], 2),
                        "min_response_time": round(row[2], 2),
                        "max_response_time": round(row[3], 2),
                        "sample_count": row[4]
                    }
                    for row in api_metrics
                ],
                "error_rates": [
                    {"date": str(row[0]), "errors": row[1]}
                    for row in error_data
                ],
                "database_metrics": [
                    {
                        "metric": row[0],
                        "avg_value": round(row[1], 2),
                        "max_value": round(row[2], 2)
                    }
                    for row in db_metrics
                ],
                "storage_metrics": {
                    "total_storage_bytes": storage_metrics[0] or 0,
                    "total_files": storage_metrics[1] or 0,
                    "avg_file_size_bytes": round(storage_metrics[2] or 0, 2)
                },
                "period_hours": hours
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    def record_system_metric(self, metric_type: str, value: float,
                           unit: str = None, labels: Dict[str, Any] = None):
        """Record a system performance metric."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO system_metrics (metric_type, metric_value, metric_unit, labels)
            VALUES (%s, %s, %s, %s)
            """, (metric_type, value, unit, labels or {}))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record system metric: {e}")

# Global instance
analytics_service = AnalyticsService()