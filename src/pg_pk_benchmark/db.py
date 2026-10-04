"""Database connection and execution utilities using psycopg3."""

from __future__ import annotations

import logging
from typing import Any
import psycopg

logger = logging.getLogger(__name__)


def get_db_connection(config: dict[str, Any]) -> psycopg.Connection:
    """Establish and return a new PostgreSQL connection."""
    try:
        conn = psycopg.connect(**config)
        return conn
    except Exception as exc:
        logger.error("Failed to connect to PostgreSQL: %s", exc)
        raise RuntimeError(f"Database connection error: {exc}") from exc


def verify_connection(config: dict[str, Any]) -> str:
    """Check database connection health and return PostgreSQL server version string."""
    with get_db_connection(config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version_str = cur.fetchone()[0]
            logger.info("Connected to PostgreSQL: %s", version_str)
            return version_str
