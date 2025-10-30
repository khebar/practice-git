"""Daily orchestration for the LinkedIn analytics ETL."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from etl_service.config import DatabaseConfig
from etl_service.fact_builder import build_daily_fact
from etl_service.postgres_etl import PostgresETLService
from linkedin.collector import LinkedInMetricsCollector


def run_daily_job() -> None:
    """Run the LinkedIn ETL workflow end-to-end."""

    db_config = DatabaseConfig.from_env()
    etl_service = PostgresETLService(db_config)
    collector = LinkedInMetricsCollector(db_config)

    metric = collector.fetch_metrics()
    collector.store_temporary(metric)

    extracted = etl_service.extract_all()
    linkedin_metrics = etl_service.extract_table("linkedin_metrics_tmp")
    if not linkedin_metrics:
        linkedin_metrics = [asdict(metric)]

    fact_rows = build_daily_fact(extracted, linkedin_metrics)
    etl_service.load_fact_rows(fact_rows)


scheduler = BlockingScheduler(timezone="UTC")


@scheduler.scheduled_job("cron", hour=2, minute=0)
def scheduled_etl() -> None:  # pragma: no cover - orchestrator entry point
    run_daily_job()
    print(f"ETL pipeline executed at {datetime.utcnow().isoformat()}Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LinkedIn ETL pipeline scheduler")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Execute the ETL immediately and exit instead of starting the scheduler.",
    )
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover - script execution guard
    cli_args = _parse_args()
    if cli_args.run_once:
        run_daily_job()
    else:
        scheduler.start()
