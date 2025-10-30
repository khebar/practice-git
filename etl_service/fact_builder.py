"""Transformation helpers for building the LinkedIn fact table."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any


def _normalize_activity_date(record: dict[str, Any]) -> date | None:
    value = record.get("activity_date") or record.get("run_date") or record.get("created_at")
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return date.fromisoformat(str(value))


def build_daily_fact(
    source_data: dict[str, list[dict[str, Any]]],
    linkedin_metrics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate raw tables into a daily fact representation."""

    daily: dict[date, dict[str, Any]] = defaultdict(
        lambda: {
            "activity_date": None,
            "run_count": 0,
            "comment_count": 0,
            "reply_count": 0,
            "connection_count": 0,
            "sent_invitations": 0,
            "received_invitations": 0,
            "profile_visits": 0,
            "profile_relationships": 0,
            "profile_views": 0,
            "search_appearances": 0,
        }
    )

    for table_name, rows in source_data.items():
        for row in rows:
            activity_date = _normalize_activity_date(row)
            if activity_date is None:
                continue
            bucket = daily[activity_date]
            bucket["activity_date"] = activity_date
            match table_name:
                case "run_logs":
                    bucket["run_count"] += 1
                case "comments":
                    bucket["comment_count"] += 1
                case "replies":
                    bucket["reply_count"] += 1
                case "connections":
                    bucket["connection_count"] += 1
                case "sent_invitations":
                    bucket["sent_invitations"] += 1
                case "received_invitations":
                    bucket["received_invitations"] += 1
                case "profile_visits":
                    bucket["profile_visits"] += 1
                case "profile_relationships":
                    bucket["profile_relationships"] += 1
                case _:
                    bucket.setdefault(f"{table_name}_count", 0)
                    bucket[f"{table_name}_count"] += 1

    for metric_row in linkedin_metrics:
        activity_date = _normalize_activity_date(metric_row)
        if activity_date is None:
            continue
        bucket = daily[activity_date]
        bucket["activity_date"] = activity_date
        bucket["profile_views"] = int(metric_row.get("profile_views", 0))
        bucket["search_appearances"] = int(metric_row.get("search_appearances", 0))

    return sorted(daily.values(), key=lambda item: item["activity_date"] or date.min)
