import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import psycopg2

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import POSTGRES_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

def get_db_connection():
    return psycopg2.connect(POSTGRES_URL)

class AnalyticsService:
    def __init__(self):
        self.db_connection = None

    def get_user_activity_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user activity metrics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Calculate date range
            start_date = datetime.now() - timedelta(days=days)

            # User login activity
            cursor.execute("""
            SELECT
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_logins,
                AVG(EXTRACT(EPOCH FROM (last_login - LAG(last_login) OVER (PARTITION BY user_id ORDER BY last_login)))) as avg_session_duration
            FROM users
            WHERE last_login >= %s
            """, (start_date,))

            login_stats = cursor.fetchone()

            # Document upload activity
            cursor.execute("""
            SELECT
                COUNT(*) as total_uploads,
                COUNT(DISTINCT uploaded_by) as active_uploaders,
                AVG(file_size) as avg_file_size
            FROM documents
            WHERE uploaded_at >= %s
            """, (start_date,))

            upload_stats = cursor.fetchone()

            # QA session activity
            cursor.execute("""
            SELECT
                COUNT(*) as total_queries,
                COUNT(DISTINCT user_id) as active_searchers,
                AVG(LENGTH(question)) as avg_question_length
            FROM qa_sessions
            WHERE timestamp >= %s
            """, (start_date,))

            qa_stats = cursor.fetchone()

            # Daily activity breakdown
            cursor.execute("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as event_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM analytics_events
            WHERE timestamp >= %s
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            """, (start_date,))

            daily_activity = cursor.fetchall()

            conn.close()

            return {
                "period_days": days,
                "user_activity": {
                    "unique_users": login_stats[0] or 0,
                    "total_logins": login_stats[1] or 0,
                    "avg_session_duration_hours": (login_stats[2] or 0) / 3600 if login_stats[2] else 0
                },
                "document_activity": {
                    "total_uploads": upload_stats[0] or 0,
                    "active_uploaders": upload_stats[1] or 0,
                    "avg_file_size_mb": (upload_stats[2] or 0) / (1024 * 1024)
                },
                "search_activity": {
                    "total_queries": qa_stats[0] or 0,
                    "active_searchers": qa_stats[1] or 0,
                    "avg_question_length": qa_stats[2] or 0
                },
                "daily_breakdown": [
                    {
                        "date": str(row[0]),
                        "events": row[1],
                        "unique_users": row[2]
                    } for row in daily_activity
                ]
            }

        except Exception as e:
            logger.error(f"User activity analytics error: {e}")
            return {"error": "Failed to generate user activity metrics"}

    def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Calculate time range
            start_time = datetime.now() - timedelta(hours=hours)

            # System metrics aggregation
            cursor.execute("""
            SELECT
                service_name,
                metric_name,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as sample_count
            FROM system_metrics
            WHERE timestamp >= %s
            GROUP BY service_name, metric_name
            ORDER BY service_name, metric_name
            """, (start_time,))

            metrics = cursor.fetchall()

            # Organize by service
            system_metrics = {}
            for row in metrics:
                service_name = row[0]
                if service_name not in system_metrics:
                    system_metrics[service_name] = []

                system_metrics[service_name].append({
                    "metric_name": row[1],
                    "avg_value": float(row[2]) if row[2] else 0,
                    "min_value": float(row[3]) if row[3] else 0,
                    "max_value": float(row[4]) if row[4] else 0,
                    "sample_count": row[5]
                })

            # Database performance
            cursor.execute("""
            SELECT
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables
            ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
            LIMIT 10
            """)

            db_stats = cursor.fetchall()

            conn.close()

            return {
                "period_hours": hours,
                "system_metrics": system_metrics,
                "database_performance": [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "inserts": row[2],
                        "updates": row[3],
                        "deletes": row[4]
                    } for row in db_stats
                ],
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return {"error": "Failed to generate system metrics"}

    def track_event(self, user_id: Optional[str], event: AnalyticsEvent, ip_address: Optional[str] = None):
        """Track an analytics event."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO analytics_events (
                user_id, event_type, event_data, session_id,
                ip_address, user_agent, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (
                user_id,
                event.event_type,
                event.event_data,
                event.session_id,
                ip_address or event.ip_address,
                event.user_agent
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Event tracking error: {e}")

    def track_system_metric(self, service_name: str, metric_name: str,
                          metric_value: float, labels: Optional[Dict[str, Any]] = None):
        """Track a system metric."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO system_metrics (
                service_name, metric_name, metric_value, labels, timestamp
            ) VALUES (%s, %s, %s, %s, NOW())
            """, (
                service_name,
                metric_name,
                metric_value,
                labels
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"System metric tracking error: {e}")

# Global instance
analytics_service = AnalyticsService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Analytics service startup")
    yield
    logger.info("Analytics service shutdown")

app = FastAPI(
    title="Analytics Service",
    description="User activity tracking and system analytics microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analytics/user-activity")
async def get_user_activity_analytics(days: int = 30, req: Request = None):
    """Get user activity analytics."""
    # Check if user has admin role (from gateway headers)
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    return analytics_service.get_user_activity_metrics(days)

@app.get("/analytics/system-metrics")
async def get_system_metrics(hours: int = 24, req: Request = None):
    """Get system performance metrics."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    return analytics_service.get_system_metrics(hours)

@app.post("/analytics/track")
async def track_analytics_event(event: AnalyticsEvent, req: Request = None):
    """Track an analytics event."""
    user_id = req.headers.get("X-User-ID") if req else None
    client_ip = req.client.host if req else None

    analytics_service.track_event(user_id, event, client_ip)
    return {"message": "Event tracked successfully"}

@app.post("/analytics/system-metric")
async def track_system_metric(
    service_name: str,
    metric_name: str,
    metric_value: float,
    labels: Optional[Dict[str, Any]] = None,
    req: Request = None
):
    """Track a system metric (inter-service endpoint)."""
    # In production, add service authentication
    analytics_service.track_system_metric(service_name, metric_name, metric_value, labels)
    return {"message": "Metric tracked successfully"}

@app.get("/analytics/dashboard")
async def get_dashboard_data(days: int = 7, req: Request = None):
    """Get dashboard data combining user activity and system metrics."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    user_activity = analytics_service.get_user_activity_metrics(days)
    system_metrics = analytics_service.get_system_metrics(24)  # Last 24 hours

    return {
        "user_activity": user_activity,
        "system_metrics": system_metrics,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)