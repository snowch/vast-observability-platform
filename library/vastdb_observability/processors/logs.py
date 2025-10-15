from typing import Dict, Any
from datetime import datetime
from vastdb_observability.models import Event
from vastdb_observability.processors.base import BaseProcessor


class LogsProcessor(BaseProcessor[Event]):
    """Processes raw log data into the unified Event model."""

    def normalize(self, raw_log: Dict[str, Any]) -> Event:
        """Normalizes a raw log dictionary into a structured Event."""
        payload = raw_log.get("payload", {})
        tags = raw_log.get("tags", {})

        # Ensure log_level is present in tags for consistent filtering
        if "log_level" not in tags:
            tags["log_level"] = "info"

        return Event(
            timestamp=self._parse_timestamp(raw_log.get("timestamp")),
            entity_id=raw_log.get("host", "unknown"),
            event_type='log',  # This processor specifically creates events of type 'log'
            source=raw_log.get("source", "unknown"),
            environment=raw_log.get("environment", "production"),
            message=self._build_message(payload),
            tags=tags,
            attributes=payload,  # Store the original, detailed payload in attributes
        )

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Safely parses a timestamp string into a datetime object."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        if isinstance(timestamp_str, str):
            try:
                # Handle ISO format with or without 'Z'
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return datetime.utcnow()
        return datetime.utcnow()

    def _build_message(self, payload: Dict[str, Any]) -> str:
        """Creates a human-readable summary message from the event payload."""
        event_type = payload.get("event_type", "unknown event")

        if event_type == "deadlocks":
            return f"Detected {payload.get('count', 0)} deadlock(s)."
        elif event_type == "connection_stats":
            return f"{payload.get('active', 0)}/{payload.get('total', 0)} active connections."
        elif event_type == "query_error":
            return f"Query error {payload.get('error_code', 'N/A')}: {payload.get('error_message', 'Unknown')}"
        
        return f"Log event of type '{event_type}' received."

    def enrich(self, event: Event) -> Event:
        """Enriches the event with additional computed tags or metadata."""
        if event.tags.get("log_level") in ["error", "critical", "alert", "emergency"]:
            event.tags["requires_alert"] = "true"

        if "deadlock" in event.attributes.get("event_type", ""):
            event.tags["category"] = "database_concurrency"
        
        return event