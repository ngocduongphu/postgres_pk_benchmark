# PostgreSQL Equality Query Performance Benchmark & RCA: `id` vs `pk_clone`

This repository provides an end-to-end performance benchmarking suite and Root Cause Analysis (RCA) report for PostgreSQL equality queries comparing Primary Keys (`id`) against non-indexed duplicate columns (`pk_clone`).

## 🛠 Project Requirements & Tech Stack

- **Python**: 3.10+
- **Database**: PostgreSQL 16 (via Docker Compose)

## 🚀 Quickstart Guide

### 1. Environment & Database Setup

Copy `.env.example` to `.env` and start the PostgreSQL container:

```bash
docker compose up -d
```

### 2. Install Project Dependencies

Install the project in editable mode using Python:

```bash
python -m pip install -e .
```

### 3. Run Benchmark Pipeline

Execute the full benchmark pipeline across 1K, 100K, 1M, and 10M rows:

```bash
python -m pg_pk_benchmark.cli run
```

### 4. Display Live Presentation Summary

Print the formatted summary table directly to the console terminal for live presentation:

```bash
python -m pg_pk_benchmark.cli summary
```

### 5. Open RCA Walkthrough HTML Report

- **Windows**: `start reports\rca_walkthrough_report.html`
- **macOS/Linux**: `open reports/rca_walkthrough_report.html`

## 📊 Summary of Findings

1. **Non-Indexed Query Bottleneck**: Searching on `pk_clone` without a B-Tree index causes PostgreSQL to execute a Sequential Scan (`Seq Scan`), scanning all data pages linearly $O(N)$. Execution duration increases up to ~234ms at 10M rows.
2. **Primary Key & B-Tree Efficiency**: Searching on Primary Key `id` uses `Index Scan`, performing $O(\log N)$ logarithmic tree traversal. Duration remains sub-millisecond (~0.02ms) regardless of scale.
3. **Index Remediation**: Creating a B-Tree index on `pk_clone` (`CREATE INDEX`) restores sub-millisecond execution duration, proving that query performance depends on physical index access paths rather than logical data values.
