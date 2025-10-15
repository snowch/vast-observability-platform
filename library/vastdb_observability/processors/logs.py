from typing import Dict, Any
from datetime import datetime
from vastdb_observability.models import ProcessedLog
from vastdb_observability.processors.base import BaseProcessor


class LogsProcessor(BaseProcessor[ProcessedLog]):
    """Process raw logs into normalized format."""

    def normalize(self, raw_log: Dict[str, Any]) -> ProcessedLog:
        """Normalize raw log format to ProcessedLog model."""
        payload = raw_log.get("payload", {})

        return ProcessedLog(
            timestamp=self._parse_timestamp(raw_log.get("timestamp")),
            source=raw_log.get("source", "unknown"),
            host=raw_log.get("host", "unknown"),
            database_name=raw_log.get("database", "unknown"),
            environment=raw_log.get("environment", "production"),
            log_level=raw_log.get("tags", {}).get("log_level", "info"),
            event_type=payload.get("event_type", "unknown"),
            message=self._build_message(payload),
            tags=raw_log.get("tags", {}),
            metadata=payload,
        )

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Parse timestamp string to datetime."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        if isinstance(timestamp_str, str):
            try:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                return datetime.utcnow()
        return datetime.utcnow()

    def _build_message(self, payload: Dict[str, Any]) -> str:
        """Build a human-readable message from payload."""
        event_type = payload.get("event_type", "unknown")

        if event_type == "deadlocks":
            count = payload.get("count", 0)
            return f"Detected {count} deadlock(s)"
        elif event_type == "connection_stats":
            total = payload.get("total", 0)
            active = payload.get("active", 0)
            return f"{active}/{total} active connections"
        elif event_type == "query_error":
            error_code = payload.get("error_code", "")
            error_msg = payload.get("error_message", "")
            return f"Query error {error_code}: {error_msg}"
        else:
            return f"Event: {event_type}"

    def enrich(self, log: ProcessedLog) -> ProcessedLog:
        """Enrich log with additional metadata."""
        if log.log_level in ["error", "critical"]:
            log.tags["requires_alert"] = "true"

        if "deadlock" in log.event_type.lower():
            log.tags["category"] = "concurrency"
        elif "connection" in log.event_type.lower():
            log.tags["category"] = "connection"
        elif "error" in log.event_type.lower():
            log.tags["category"] = "error"

        severity_map = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}
        log.metadata["severity_score"] = severity_map.get(log.log_level, 1)

        return log
