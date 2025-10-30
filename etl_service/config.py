"""Configuration helpers for the ETL service."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Runtime configuration for connecting to Postgres."""

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "analytics"
    options: str | None = None

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Build a :class:`DatabaseConfig` from environment variables.

        The following variables are supported:
        - ``PGHOST``
        - ``PGPORT``
        - ``PGUSER``
        - ``PGPASSWORD``
        - ``PGDATABASE``
        - ``PGOPTIONS``
        """

        return cls(
            host=os.environ.get("PGHOST", cls.host),
            port=int(os.environ.get("PGPORT", cls.port)),
            user=os.environ.get("PGUSER", cls.user),
            password=os.environ.get("PGPASSWORD", cls.password),
            database=os.environ.get("PGDATABASE", cls.database),
            options=os.environ.get("PGOPTIONS"),
        )


DEFAULT_TABLES = (
    "run_logs",
    "daily_activity",
    "comments",
    "replies",
    "connections",
    "sent_invitations",
    "received_invitations",
    "profile_visits",
    "profile_relationships",
)
