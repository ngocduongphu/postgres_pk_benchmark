"""Configuration settings and environment variable loading."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_REPORT_PATH = REPORTS_DIR / "benchmark_results.csv"
RAW_CSV_PATH = REPORTS_DIR / "benchmark_raw.csv"
HTML_REPORT_PATH = REPORTS_DIR / "rca_walkthrough_report.html"

TABLE_NAME = "user_records"
INDEX_NAME = "idx_user_records_pk_clone"

DATASET_SCALES: dict[str, int] = {
    "1K": 1_000,
    "100K": 100_000,
    "1M": 1_000_000,
    "10M": 10_000_000,
}

WARMUP_RUNS = 2
MEASURED_RUNS = 10


def get_db_config() -> dict[str, str | int]:
    """Retrieve PostgreSQL connection parameter map from environment."""
    return {
        "dbname": os.getenv("POSTGRES_DB", "user_benchmark_db"),
        "user": os.getenv("POSTGRES_USER", "benchmark_admin"),
        "password": os.getenv("POSTGRES_PASSWORD", "benchmark_secret_pass"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
    }
