"""Database utilities for the ETL service."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection as _Connection

from .config import DatabaseConfig


@contextmanager
def get_connection(config: DatabaseConfig) -> Iterator[_Connection]:
    """Yield a Postgres connection configured for autocommit workloads."""

    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        dbname=config.database,
        options=config.options,
    )
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
