"""SQLite database interface for storing posts, queues, and publish history."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import settings


class Database:
    """Manages local SQLite database operations."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or settings.DB_PATH)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Posts Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    brand_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    input_type TEXT DEFAULT 'general',
                    content_json TEXT NOT NULL,
                    images_json TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Scheduled Queue Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    platforms TEXT NOT NULL,
                    scheduled_time TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'pending',
                    executed_at TIMESTAMP,
                    log_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
                """
            )

            # Publish Logs Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS publish_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_payload TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()

    def save_post(
        self,
        post_id: str,
        brand_id: str,
        topic: str,
        content: Dict[str, Any],
        images: Optional[Dict[str, str]] = None,
        input_type: str = "general",
        status: str = "draft",
    ) -> str:
        """Save a generated post to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO posts (id, brand_id, topic, input_type, content_json, images_json, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    topic = excluded.topic,
                    content_json = excluded.content_json,
                    images_json = excluded.images_json,
                    status = excluded.status
                """,
                (
                    post_id,
                    brand_id,
                    topic,
                    input_type,
                    json.dumps(content, ensure_ascii=False),
                    json.dumps(images or {}, ensure_ascii=False),
                    status,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            return post_id

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single post by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["content"] = json.loads(data["content_json"])
            data["images"] = json.loads(data["images_json"] or "{}")
            return data

    def list_posts(
        self,
        brand_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List posts with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM posts WHERE 1=1"
            params: List[Any] = []

            if brand_id:
                query += " AND brand_id = ?"
                params.append(brand_id)
            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                item["content"] = json.loads(item["content_json"])
                item["images"] = json.loads(item["images_json"] or "{}")
                results.append(item)
            return results

    def update_post_status(self, post_id: str, status: str) -> None:
        """Update the publishing status of a post."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE posts SET status = ? WHERE id = ?", (status, post_id))
            conn.commit()

    def schedule_post(
        self,
        post_id: str,
        brand_id: str,
        platforms: List[str],
        scheduled_time: str,
    ) -> int:
        """Queue a post for future or automated publishing."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scheduled_queue (post_id, brand_id, platforms, scheduled_time, status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (post_id, brand_id, json.dumps(platforms), scheduled_time),
            )
            job_id = cursor.lastrowid or 0
            cursor.execute("UPDATE posts SET status = 'scheduled' WHERE id = ?", (post_id,))
            conn.commit()
            return job_id

    def get_pending_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve all scheduled posts ready to be published."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sq.*, p.topic, p.content_json, p.images_json
                FROM scheduled_queue sq
                JOIN posts p ON sq.post_id = p.id
                WHERE sq.status = 'pending' AND sq.scheduled_time <= ?
                ORDER BY sq.scheduled_time ASC
                """,
                (now_str,),
            )
            jobs = []
            for row in cursor.fetchall():
                item = dict(row)
                item["platforms"] = json.loads(item["platforms"])
                item["content"] = json.loads(item["content_json"])
                item["images"] = json.loads(item["images_json"] or "{}")
                jobs.append(item)
            return jobs

    def mark_job_status(self, job_id: int, status: str, log_message: str = "") -> None:
        """Update execution status of a scheduled job."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE scheduled_queue
                SET status = ?, executed_at = ?, log_message = ?
                WHERE id = ?
                """,
                (status, now_str, log_message, job_id),
            )
            conn.commit()

    def log_publish(
        self,
        post_id: str,
        brand_id: str,
        platform: str,
        status: str,
        response_payload: Any,
    ) -> None:
        """Record a publishing attempt in the audit log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO publish_logs (post_id, brand_id, platform, status, response_payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    brand_id,
                    platform,
                    status,
                    json.dumps(response_payload, ensure_ascii=False)
                    if isinstance(response_payload, (dict, list))
                    else str(response_payload),
                ),
            )
            conn.commit()

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent publishing logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM publish_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Aggregate stats for dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM posts WHERE status = 'published'")
            published_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM scheduled_queue WHERE status = 'pending'")
            pending_queue = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM publish_logs WHERE status LIKE '%success%'"
            )
            successful_publishes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM publish_logs WHERE status = 'failed'")
            failed_publishes = cursor.fetchone()[0]

            return {
                "total_posts": total_posts,
                "published_posts": published_posts,
                "pending_queue": pending_queue,
                "successful_publishes": successful_publishes,
                "failed_publishes": failed_publishes,
            }


db = Database()
