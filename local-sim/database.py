"""SQLite persistence for the local service-request simulation."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


FINAL_STATUSES = {"Approved", "Rejected"}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS service_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    ai_summary TEXT NOT NULL,
                    suggested_reply TEXT NOT NULL,
                    ai_mode TEXT NOT NULL DEFAULT 'simulated',
                    status TEXT NOT NULL DEFAULT 'Awaiting review',
                    review_comment TEXT,
                    reviewed_by TEXT,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    CHECK (status IN ('Awaiting review', 'Approved', 'Rejected'))
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_requests_status_created "
                "ON service_requests(status, created_at DESC)"
            )
            for operation in ("INSERT", "UPDATE"):
                connection.execute(
                    f"""
                    CREATE TRIGGER IF NOT EXISTS validate_service_requests_{operation.lower()}
                    BEFORE {operation} ON service_requests
                    WHEN
                        length(trim(NEW.title)) NOT BETWEEN 1 AND 120 OR
                        length(NEW.description) NOT BETWEEN 20 AND 2000 OR
                        length(trim(NEW.requester)) NOT BETWEEN 1 AND 120 OR
                        NEW.category NOT IN (
                            'Access', 'Hardware', 'Software',
                            'Microsoft 365', 'Network', 'Other'
                        ) OR
                        NEW.priority NOT IN ('Low', 'Medium', 'High', 'Critical') OR
                        length(trim(NEW.ai_summary)) NOT BETWEEN 1 AND 500 OR
                        length(trim(NEW.suggested_reply)) NOT BETWEEN 1 AND 1200 OR
                        NEW.ai_mode != 'simulated' OR
                        NEW.status NOT IN ('Awaiting review', 'Approved', 'Rejected') OR
                        length(coalesce(NEW.review_comment, '')) > 1000 OR
                        length(coalesce(NEW.reviewed_by, '')) > 120 OR
                        (
                            NEW.status = 'Awaiting review' AND
                            (NEW.reviewed_by IS NOT NULL OR NEW.reviewed_at IS NOT NULL)
                        ) OR
                        (
                            NEW.status IN ('Approved', 'Rejected') AND
                            (NEW.reviewed_by IS NULL OR NEW.reviewed_at IS NULL)
                        ) OR
                        (
                            NEW.status = 'Rejected' AND
                            length(trim(coalesce(NEW.review_comment, ''))) = 0
                        )
                    BEGIN
                        SELECT RAISE(ABORT, 'service request integrity check failed');
                    END
                    """
                )

    def create_request(self, values: dict[str, Any]) -> dict[str, Any]:
        created_at = utc_now()
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO service_requests (
                    title, description, requester, category, priority,
                    ai_summary, suggested_reply, ai_mode, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'simulated', 'Awaiting review', ?)
                """,
                (
                    values["title"],
                    values["description"],
                    values["requester"],
                    values["category"],
                    values["priority"],
                    values["summary"],
                    values["suggested_reply"],
                    created_at,
                ),
            )
            request_id = cursor.lastrowid
        return self.get_request(request_id)

    def get_request(self, request_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM service_requests WHERE id = ?", (request_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_requests(self, status: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM service_requests"
        parameters: tuple[Any, ...] = ()
        if status:
            sql += " WHERE status = ?"
            parameters = (status,)
        sql += " ORDER BY id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def review_request(
        self,
        request_id: int,
        *,
        status: str,
        reviewed_by: str,
        review_comment: str,
        category: str,
        priority: str,
        ai_summary: str,
        suggested_reply: str,
    ) -> dict[str, Any] | None:
        if status not in FINAL_STATUSES:
            raise ValueError(f"Unsupported final status: {status}")

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT status FROM service_requests WHERE id = ?", (request_id,)
            ).fetchone()
            if current is None:
                return None
            if current["status"] != "Awaiting review":
                raise RuntimeError("This request has already been reviewed.")
            connection.execute(
                """
                UPDATE service_requests
                SET status = ?, reviewed_by = ?, review_comment = ?,
                    category = ?, priority = ?, ai_summary = ?,
                    suggested_reply = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    reviewed_by,
                    review_comment or None,
                    category,
                    priority,
                    ai_summary,
                    suggested_reply,
                    utc_now(),
                    request_id,
                ),
            )
        return self.get_request(request_id)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()
