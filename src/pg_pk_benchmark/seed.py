"""Database schema management and fast bulk data seeding via generate_series()."""

from __future__ import annotations

import logging
import psycopg
from .config import INDEX_NAME, TABLE_NAME

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGINT PRIMARY KEY,
    pk_clone BIGINT NOT NULL
);
"""


def setup_schema(conn: psycopg.Connection) -> None:
    """Create the benchmark table if it does not exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Table '%s' initialized.", TABLE_NAME)


def check_index_exists(conn: psycopg.Connection, index_name: str = INDEX_NAME) -> bool:
    """Check whether a specific index exists in pg_indexes catalog."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s;", (index_name,))
        return cur.fetchone() is not None


def create_pk_clone_index(conn: psycopg.Connection) -> None:
    """Create B-Tree index on pk_clone column."""
    if check_index_exists(conn, INDEX_NAME):
        logger.info("Index '%s' already exists.", INDEX_NAME)
        return
    logger.info("Creating B-Tree index '%s' on column 'pk_clone'...", INDEX_NAME)
    with conn.cursor() as cur:
        cur.execute(f"CREATE INDEX {INDEX_NAME} ON {TABLE_NAME}(pk_clone);")
    conn.commit()
    logger.info("Index '%s' successfully created.", INDEX_NAME)


def drop_pk_clone_index(conn: psycopg.Connection) -> None:
    """Drop the B-Tree index on pk_clone column if present."""
    if not check_index_exists(conn, INDEX_NAME):
        return
    with conn.cursor() as cur:
        cur.execute(f"DROP INDEX IF EXISTS {INDEX_NAME};")
    conn.commit()
    logger.info("Dropped index '%s'.", INDEX_NAME)


def run_analyze(conn: psycopg.Connection) -> None:
    """Execute ANALYZE command to update system catalog (pg_statistic) statistics."""
    logger.info("Executing ANALYZE on table '%s' to update statistics...", TABLE_NAME)
    with conn.cursor() as cur:
        cur.execute(f"ANALYZE {TABLE_NAME};")
    conn.commit()
    logger.info("ANALYZE complete. Planner statistics updated.")


def clear_table_data(conn: psycopg.Connection) -> None:
    """Truncate the benchmark table."""
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {TABLE_NAME};")
    conn.commit()


def seed_dataset_scale(conn: psycopg.Connection, scale_name: str, target_count: int) -> int:
    """Bulk seed table using generate_series() for high efficiency."""
    logger.info("Seeding scale '%s' (%s rows)...", scale_name, f"{target_count:,}")
    drop_pk_clone_index(conn)
    clear_table_data(conn)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {TABLE_NAME} (id, pk_clone)
            SELECT gs, gs
            FROM generate_series(1, %s) AS gs;
            """,
            (target_count,),
        )
        inserted_rows = cur.rowcount

    conn.commit()
    logger.info("Successfully seeded %s rows.", f"{inserted_rows:,}")
    return inserted_rows
