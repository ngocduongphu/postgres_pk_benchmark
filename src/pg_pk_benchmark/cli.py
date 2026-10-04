"""Command Line Interface (CLI) entry point for project execution."""

from __future__ import annotations

import argparse
import logging
import sys
import pandas as pd

from . import __version__
from .config import CSV_REPORT_PATH, get_db_config
from .db import get_db_connection, verify_connection
from .runner import run_full_benchmark_suite
from .seed import setup_schema
from .report import print_terminal_summary, process_and_save_reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def command_run(args: argparse.Namespace) -> None:
    """Execute full benchmark pipeline: schema setup -> seed -> benchmark -> report."""
    db_config = get_db_config()
    logger.info("Step 1/4: Verifying PostgreSQL connection...")
    pg_version = verify_connection(db_config)

    with get_db_connection(db_config) as conn:
        logger.info("Step 2/4: Setting up database schema...")
        setup_schema(conn)

        logger.info("Step 3/4: Executing benchmark matrix (1K -> 100K -> 1M -> 10M)...")
        raw_records = run_full_benchmark_suite(conn)

    logger.info("Step 4/4: Exporting benchmark results & HTML report...")
    df_summary, _ = process_and_save_reports(raw_records, pg_version)
    print_terminal_summary(df_summary)


def command_summary(args: argparse.Namespace) -> None:
    """Print ASCII summary table from existing CSV report."""
    if not CSV_REPORT_PATH.exists():
        logger.error("No CSV report found at %s. Please run `uv run benchmark run` first.", CSV_REPORT_PATH)
        sys.exit(1)
    df_summary = pd.read_csv(CSV_REPORT_PATH)
    print_terminal_summary(df_summary)


def main() -> None:
    """CLI Entry point."""
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="PostgreSQL Equality Query Performance Benchmark & RCA",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub_run = subparsers.add_parser("run", help="Run full pipeline (seed, benchmark, CSV/HTML generation)")
    sub_run.set_defaults(func=command_run)

    sub_sum = subparsers.add_parser("summary", help="Print terminal ASCII summary table")
    sub_sum.set_defaults(func=command_summary)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
