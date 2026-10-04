"""Execution profiling and EXPLAIN ANALYZE result parser."""

from __future__ import annotations

import logging
from typing import Any
import psycopg
from .config import DATASET_SCALES, MEASURED_RUNS, TABLE_NAME, WARMUP_RUNS
from .seed import create_pk_clone_index, drop_pk_clone_index, run_analyze, seed_dataset_scale

logger = logging.getLogger(__name__)


def execute_explain_analyze(conn: psycopg.Connection, query: str, params: tuple[Any, ...]) -> dict[str, Any]:
    """Execute EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) and extract execution node statistics."""
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

    with conn.cursor() as cur:
        cur.execute(explain_query, params)
        result = cur.fetchone()[0]

    plan_wrapper = result[0]
    execution_time_ms = float(plan_wrapper.get("Execution Time", 0.0))
    planning_time_ms = float(plan_wrapper.get("Planning Time", 0.0))
    top_node = plan_wrapper.get("Plan", {})

    scan_type = top_node.get("Node Type", "Unknown")
    shared_hit_blocks = float(top_node.get("Shared Hit Blocks", 0))
    shared_read_blocks = float(top_node.get("Shared Read Blocks", 0))

    return {
        "execution_time_ms": execution_time_ms,
        "planning_time_ms": planning_time_ms,
        "scan_type": scan_type,
        "shared_hit_blocks": shared_hit_blocks,
        "shared_read_blocks": shared_read_blocks,
    }


def benchmark_single_scenario(
    conn: psycopg.Connection,
    scale_label: str,
    row_count: int,
    scenario_label: str,
    column_name: str,
    is_indexed: bool,
    target_value: int,
) -> list[dict[str, Any]]:
    """Execute warm-up and measured runs for a specific query scenario."""
    query = f"SELECT id, pk_clone FROM {TABLE_NAME} WHERE {column_name} = %s;"
    params = (target_value,)

    # Warm-up execution
    for _ in range(WARMUP_RUNS):
        execute_explain_analyze(conn, query, params)

    records = []
    for run_idx in range(1, MEASURED_RUNS + 1):
        metrics = execute_explain_analyze(conn, query, params)
        metrics.update(
            {
                "dataset": scale_label,
                "row_count": row_count,
                "scenario": scenario_label,
                "target_column": column_name,
                "is_indexed": "Yes" if is_indexed else "No",
                "run_index": run_idx,
            }
        )
        records.append(metrics)

    return records


def run_full_benchmark_suite(conn: psycopg.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run full benchmark matrix across 4 dataset scales and 3 scenarios."""
    raw_measurements: list[dict[str, Any]] = []

    for scale_label, row_count in DATASET_SCALES.items():
        logger.info("=== Starting Benchmark Matrix for Scale: %s (%s rows) ===", scale_label, f"{row_count:,}")

        # Seed data
        seed_dataset_scale(conn, scale_label, row_count)
        run_analyze(conn)

        target_value = row_count // 2  # Query target near middle of table

        # Scenario 1: Primary Key (id)
        logger.info("Running Scenario 1: PK (id)...")
        pk_runs = benchmark_single_scenario(
            conn, scale_label, row_count, "1. Primary Key (id)", "id", True, target_value
        )
        raw_measurements.extend(pk_runs)

        # Scenario 2: pk_clone Without Index
        logger.info("Running Scenario 2: pk_clone (No Index)...")
        drop_pk_clone_index(conn)
        run_analyze(conn)
        no_idx_runs = benchmark_single_scenario(
            conn, scale_label, row_count, "2. pk_clone (No Index)", "pk_clone", False, target_value
        )
        raw_measurements.extend(no_idx_runs)

        # Scenario 3: pk_clone With Index
        logger.info("Running Scenario 3: pk_clone (With Index)...")
        create_pk_clone_index(conn)
        run_analyze(conn)
        idx_runs = benchmark_single_scenario(
            conn, scale_label, row_count, "3. pk_clone (With B-Tree Index)", "pk_clone", True, target_value
        )
        raw_measurements.extend(idx_runs)

    return raw_measurements
