import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from config.config import POSTGRES_URL

logger = logging.getLogger(__name__)

class CollaborationService:
    def __init__(self):
        self.db_url = POSTGRES_URL

    def create_document_version(self, doc_id: str, version_number: int,
                               content_hash: str, changes_summary: str = None,
                               created_by: str = None) -> bool:
        """Create a new document version for tracking changes."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO document_versions (doc_id, version_number, content_hash, changes_summary, created_by)
            VALUES (%s, %s, %s, %s, %s)
            """, (doc_id, version_number, content_hash, changes_summary, created_by))
            conn.commit()
            conn.close()
            logger.info(f"Created version {version_number} for document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create document version: {e}")
            return False

    def get_document_versions(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a document."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, version_number, content_hash, changes_summary, created_by, created_at
            FROM document_versions
            WHERE doc_id = %s
            ORDER BY version_number DESC
            """, (doc_id,))

            versions = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": str(row[0]),
                    "version_number": row[1],
                    "content_hash": row[2],
                    "changes_summary": row[3],
                    "created_by": str(row[4]) if row[4] else None,
                    "created_at": row[5].isoformat() if row[5] else None
                }
                for row in versions
            ]
        except Exception as e:
            logger.error(f"Failed to get document versions: {e}")
            return []

    def add_document_comment(self, doc_id: str, content: str, author_id: str,
                           parent_comment_id: str = None, position_data: Dict[str, Any] = None,
                           comment_type: str = 'text') -> Optional[str]:
        """Add a comment to a document."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO document_comments (doc_id, parent_comment_id, content, author_id, position_data, comment_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (doc_id, parent_comment_id, content, author_id, position_data, comment_type))

            comment_id = str(cursor.fetchone()[0])
            conn.commit()
            conn.close()

            logger.info(f"Added comment {comment_id} to document {doc_id}")
            return comment_id
        except Exception as e:
            logger.error(f"Failed to add document comment: {e}")
            return None

    def get_document_comments(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a document."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT
                c.id, c.content, c.author_id, c.position_data, c.comment_type,
                c.is_resolved, c.created_at, c.updated_at,
                u.email as author_email,
                p.content as parent_content
            FROM document_comments c
            LEFT JOIN users u ON c.author_id = u.id
            LEFT JOIN document_comments p ON c.parent_comment_id = p.id
            WHERE c.doc_id = %s
            ORDER BY c.created_at ASC
            """, (doc_id,))

            comments = cursor.fetchall()
            conn.close()

            # Build comment tree
            comment_dict = {}
            root_comments = []

            for row in comments:
                comment = {
                    "id": str(row[0]),
                    "content": row[1],
                    "author_id": str(row[2]),
                    "author_email": row[8],
                    "position_data": row[3],
                    "comment_type": row[4],
                    "is_resolved": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                    "parent_content": row[9],
                    "replies": []
                }
                comment_dict[comment["id"]] = comment

            # Build hierarchy
            for comment in comment_dict.values():
                if comment.get("parent_comment_id"):
                    parent_id = comment["parent_comment_id"]
                    if parent_id in comment_dict:
                        comment_dict[parent_id]["replies"].append(comment)
                    else:
                        root_comments.append(comment)
                else:
                    root_comments.append(comment)

            return root_comments
        except Exception as e:
            logger.error(f"Failed to get document comments: {e}")
            return []

    def update_comment_status(self, comment_id: str, is_resolved: bool, user_id: str) -> bool:
        """Update comment resolution status."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE document_comments
            SET is_resolved = %s, updated_at = NOW()
            WHERE id = %s
            """, (is_resolved, comment_id))
            conn.commit()
            conn.close()

            logger.info(f"Updated comment {comment_id} resolution status to {is_resolved}")
            return True
        except Exception as e:
            logger.error(f"Failed to update comment status: {e}")
            return False

    def get_document_collaboration_status(self, doc_id: str) -> Dict[str, Any]:
        """Get comprehensive collaboration status for a document."""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Get comment statistics
            cursor.execute("""
            SELECT
                COUNT(*) as total_comments,
                COUNT(CASE WHEN is_resolved = true THEN 1 END) as resolved_comments,
                COUNT(DISTINCT author_id) as unique_contributors,
                MAX(created_at) as last_activity
            FROM document_comments
            WHERE doc_id = %s
            """, (doc_id,))

            comment_stats = cursor.fetchone()

            # Get version information
            cursor.execute("""
            SELECT COUNT(*), MAX(version_number), MAX(created_at)
            FROM document_versions
            WHERE doc_id = %s
            """, (doc_id,))

            version_stats = cursor.fetchone()

            conn.close()

            return {
                "total_comments": comment_stats[0] or 0,
                "resolved_comments": comment_stats[1] or 0,
                "unresolved_comments": (comment_stats[0] or 0) - (comment_stats[1] or 0),
                "unique_contributors": comment_stats[2] or 0,
                "last_activity": comment_stats[3].isoformat() if comment_stats[3] else None,
                "total_versions": version_stats[0] or 0,
                "current_version": version_stats[1] or 0,
                "last_version_date": version_stats[2].isoformat() if version_stats[2] else None
            }
        except Exception as e:
            logger.error(f"Failed to get collaboration status: {e}")
            return {
                "total_comments": 0,
                "resolved_comments": 0,
                "unresolved_comments": 0,
                "unique_contributors": 0,
                "last_activity": None,
                "total_versions": 0,
                "current_version": 0,
                "last_version_date": None
            }

# WebSocket event handlers for real-time collaboration
def handle_collaboration_event(event_type: str, data: Dict[str, Any], emit_callback):
    """Handle real-time collaboration events via WebSocket."""
    try:
        if event_type == "join_document":
            # User joined document collaboration
            doc_id = data.get("doc_id")
            user_id = data.get("user_id")
            emit_callback("user_joined", {
                "doc_id": doc_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }, room=doc_id)

        elif event_type == "leave_document":
            # User left document collaboration
            doc_id = data.get("doc_id")
            user_id = data.get("user_id")
            emit_callback("user_left", {
                "doc_id": doc_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }, room=doc_id)

        elif event_type == "add_comment":
            # New comment added
            doc_id = data.get("doc_id")
            comment_data = data.get("comment")
            emit_callback("comment_added", {
                "doc_id": doc_id,
                "comment": comment_data,
                "timestamp": datetime.now().isoformat()
            }, room=doc_id)

        elif event_type == "update_comment":
            # Comment updated
            doc_id = data.get("doc_id")
            comment_id = data.get("comment_id")
            updates = data.get("updates")
            emit_callback("comment_updated", {
                "doc_id": doc_id,
                "comment_id": comment_id,
                "updates": updates,
                "timestamp": datetime.now().isoformat()
            }, room=doc_id)

        elif event_type == "cursor_position":
            # User cursor position update
            doc_id = data.get("doc_id")
            user_id = data.get("user_id")
            position = data.get("position")
            emit_callback("cursor_moved", {
                "doc_id": doc_id,
                "user_id": user_id,
                "position": position,
                "timestamp": datetime.now().isoformat()
            }, room=doc_id)

    except Exception as e:
        logger.error(f"Failed to handle collaboration event: {e}")

# Global instance
collaboration_service = CollaborationService()