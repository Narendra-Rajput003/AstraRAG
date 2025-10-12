import sys
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
import psycopg2

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.security_audit import security_audit_service
from config.config import POSTGRES_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(POSTGRES_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Admin service startup")
    yield
    logger.info("Admin service shutdown")

app = FastAPI(
    title="Admin Service",
    description="Administrative operations and security audit microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "admin-service",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/admin/security-audit")
async def run_security_audit(req: Request = None):
    """Run comprehensive security audit (superadmin only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        audit_results = security_audit_service.run_comprehensive_security_audit()
        return audit_results
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        raise HTTPException(status_code=500, detail="Security audit failed")

@app.get("/admin/security-audit/summary")
async def get_security_audit_summary(req: Request = None):
    """Get security audit summary (admin+ only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role not in ['admin', 'superadmin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        audit_results = security_audit_service.run_comprehensive_security_audit()
        # Return only summary for regular admins
        return {
            "timestamp": audit_results["timestamp"],
            "overall_score": audit_results["overall_score"],
            "critical_issues_count": len(audit_results["critical_issues"]),
            "high_issues_count": len(audit_results["high_issues"]),
            "medium_issues_count": len(audit_results["medium_issues"]),
            "low_issues_count": len(audit_results["low_issues"]),
            "passed_checks_count": len(audit_results["passed_checks"])
        }
    except Exception as e:
        logger.error(f"Security audit summary failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security audit summary")

@app.get("/admin/users")
async def get_users(req: Request = None):
    """Get all users (superadmin only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role, is_active, last_login FROM users ORDER BY email")
        users = cursor.fetchall()
        conn.close()

        return [
            {
                "user_id": str(row[0]),
                "email": row[1],
                "role": row[2],
                "is_active": row[3],
                "last_login": row[4].isoformat() if row[4] else None
            } for row in users
        ]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/admin/users/{user_id}/status")
async def update_user_status(user_id: str, is_active: bool, req: Request = None):
    """Update user active status (superadmin only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET is_active = %s WHERE id = %s
        RETURNING id, email
        """, (is_active, user_id))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "message": f"User {result[1]} {'activated' if is_active else 'deactivated'} successfully",
            "user_id": user_id,
            "is_active": is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    req: Request = None
):
    """Get audit logs (superadmin only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = """
        SELECT id, actor_id, action, target, meta, ip, created_at
        FROM audit_logs
        WHERE 1=1
        """
        params = []

        if actor_id:
            query += " AND actor_id = %s"
            params.append(actor_id)

        if action:
            query += " AND action = %s"
            params.append(action)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        logs = cursor.fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
        count_params = []
        if actor_id:
            count_query += " AND actor_id = %s"
            count_params.append(actor_id)
        if action:
            count_query += " AND action = %s"
            count_params.append(action)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "logs": [
                {
                    "id": str(row[0]),
                    "actor_id": str(row[1]) if row[1] else None,
                    "action": row[2],
                    "target": row[3],
                    "meta": row[4] or {},
                    "ip": row[5],
                    "created_at": row[6].isoformat() if row[6] else None
                } for row in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/system-info")
async def get_system_info(req: Request = None):
    """Get system information and statistics (superadmin only)."""
    user_role = req.headers.get("X-User-Role") if req else None
    if user_role != 'superadmin':
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Database statistics
        cursor.execute("""
        SELECT
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_rows,
            n_dead_tup as dead_rows
        FROM pg_stat_user_tables
        ORDER BY schemaname, tablename
        """)

        db_stats = cursor.fetchall()

        # User role distribution
        cursor.execute("""
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
        ORDER BY count DESC
        """)

        role_stats = cursor.fetchall()

        # Document status distribution
        cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM documents
        GROUP BY status
        ORDER BY count DESC
        """)

        doc_stats = cursor.fetchall()

        conn.close()

        return {
            "database_stats": [
                {
                    "schema": row[0],
                    "table": row[1],
                    "inserts": row[2],
                    "updates": row[3],
                    "deletes": row[4],
                    "live_rows": row[5],
                    "dead_rows": row[6]
                } for row in db_stats
            ],
            "user_role_distribution": [
                {"role": row[0], "count": row[1]} for row in role_stats
            ],
            "document_status_distribution": [
                {"status": row[0], "count": row[1]} for row in doc_stats
            ],
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)