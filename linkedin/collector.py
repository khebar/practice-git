"""LinkedIn data collection utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from psycopg2 import sql

from etl_service.config import DatabaseConfig
from etl_service.database import get_connection


@dataclass(slots=True)
class LinkedInMetric:
    activity_date: datetime
    profile_views: int
    search_appearances: int


class LinkedInMetricsCollector:
    """Collect metrics from LinkedIn and store them in a temporary table."""

    METRICS_ENDPOINT = "https://www.linkedin.com/voyager/api/identity/profiles/me"

    def __init__(self, db_config: DatabaseConfig, session: requests.Session | None = None) -> None:
        self.db_config = db_config
        self.session = session or requests.Session()

    def fetch_metrics(self) -> LinkedInMetric:
        """Fetch the latest metrics using the unofficial LinkedIn API."""

        headers = {
            "Accept": "application/json",
            "X-RestLi-Protocol-Version": "2.0.0",
            "Csrf-Token": self.session.cookies.get("JSESSIONID", ""),
        }
        response = self.session.get(self.METRICS_ENDPOINT, headers=headers, timeout=30)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        insights = payload.get("included", [{}])[0]
        return LinkedInMetric(
            activity_date=datetime.now(timezone.utc),
            profile_views=int(insights.get("profileViews", 0)),
            search_appearances=int(insights.get("searchAppearances", 0)),
        )

    def store_temporary(self, metric: LinkedInMetric, temp_table: str = "linkedin_metrics_tmp") -> None:
        """Persist the metric into a temporary Postgres table."""

        create_query = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {schema}.{table} (
                activity_date TIMESTAMPTZ PRIMARY KEY,
                profile_views INTEGER NOT NULL,
                search_appearances INTEGER NOT NULL
            )
            """
        ).format(sql.Identifier("staging"), sql.Identifier(temp_table))

        upsert_query = sql.SQL(
            """
            INSERT INTO {schema}.{table} (activity_date, profile_views, search_appearances)
            VALUES (%s, %s, %s)
            ON CONFLICT (activity_date) DO UPDATE
            SET profile_views = EXCLUDED.profile_views,
                search_appearances = EXCLUDED.search_appearances
            """
        ).format(sql.Identifier("staging"), sql.Identifier(temp_table))

        with get_connection(self.db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(create_query)
                cur.execute(
                    upsert_query,
                    (metric.activity_date, metric.profile_views, metric.search_appearances),
                )
