"""Implementation of the ETL service for Postgres sources."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from psycopg2 import sql

from .config import DEFAULT_TABLES, DatabaseConfig
from .database import get_connection


class PostgresETLService:
    """Extract, transform and load data from operational tables."""

    def __init__(
        self,
        config: DatabaseConfig,
        source_tables: Iterable[str] | None = None,
        staging_schema: str = "staging",
        fact_schema: str = "analytics",
        fact_table: str = "fact_linkedin_activity",
    ) -> None:
        self.config = config
        self.source_tables = tuple(source_tables or DEFAULT_TABLES)
        self.staging_schema = staging_schema
        self.fact_schema = fact_schema
        self.fact_table = fact_table

    def extract_table(self, table_name: str) -> list[dict[str, Any]]:
        """Return all rows from ``table_name`` as dictionaries."""

        query = sql.SQL("SELECT * FROM {}.{}").format(
            sql.Identifier(self.staging_schema), sql.Identifier(table_name)
        )
        with get_connection(self.config) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def extract_all(self) -> dict[str, list[dict[str, Any]]]:
        """Extract all configured tables at once."""

        return {table: self.extract_table(table) for table in self.source_tables}

    def load_staging_snapshot(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Load a list of dictionaries into the staging schema."""

        if not rows:
            return

        columns = tuple(rows[0].keys())
        insert_query = sql.SQL(
            "INSERT INTO {}.{} ({}) VALUES ({})"
        ).format(
            sql.Identifier(self.staging_schema),
            sql.Identifier(table_name),
            sql.SQL(", ").join(sql.Identifier(col) for col in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )

        with get_connection(self.config) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    insert_query.as_string(conn),
                    [tuple(row[col] for col in columns) for row in rows],
                )

    def load_fact_rows(self, rows: list[dict[str, Any]]) -> None:
        """Upsert aggregated rows into the fact table."""

        if not rows:
            return

        columns = tuple(rows[0].keys())
        assignments = sql.SQL(", ").join(
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
            for col in columns
            if col != "activity_date"
        )
        insert_query = sql.SQL(
            """
            INSERT INTO {schema}.{table} ({columns})
            VALUES ({placeholders})
            ON CONFLICT (activity_date) DO UPDATE SET {assignments}
            """
        ).format(
            schema=sql.Identifier(self.fact_schema),
            table=sql.Identifier(self.fact_table),
            columns=sql.SQL(", ").join(sql.Identifier(col) for col in columns),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            assignments=assignments,
        )

        with get_connection(self.config) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    insert_query.as_string(conn),
                    [tuple(row[col] for col in columns) for row in rows],
                )
