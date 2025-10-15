from typing import Dict, Any, Optional
from datetime import datetime
from vastdb_observability.models import ProcessedQuery
from vastdb_observability.processors.base import BaseProcessor


class QueriesProcessor(BaseProcessor[ProcessedQuery]):
    """Process raw query analytics into normalized format."""

    def normalize(self, raw_query: Dict[str, Any]) -> ProcessedQuery:
        """Normalize raw query format to ProcessedQuery model."""
        payload = raw_query.get("payload", {})
        query_text = payload.get("query", "")

        return ProcessedQuery(
            timestamp=self._parse_timestamp(raw_query.get("timestamp")),
            source=raw_query.get("source", "unknown"),
            host=raw_query.get("host", "unknown"),
            database_name=raw_query.get("database", "unknown"),
            environment=raw_query.get("environment", "production"),
            query_id=str(payload.get("queryid", "")),
            query_text=query_text[:500] if query_text else None,
            query_hash=ProcessedQuery.compute_query_hash(query_text) if query_text else None,
            calls=int(payload.get("calls", 0)),
            total_time_ms=float(payload.get("total_time_ms", 0.0)),
            mean_time_ms=float(payload.get("mean_time_ms", 0.0)),
            min_time_ms=self._safe_float(payload.get("min_time_ms")),
            max_time_ms=self._safe_float(payload.get("max_time_ms")),
            stddev_time_ms=self._safe_float(payload.get("stddev_time_ms")),
            rows_affected=self._safe_int(payload.get("rows")),
            cache_hit_ratio=self._safe_float(payload.get("cache_hit_ratio")),
            tags=raw_query.get("tags", {}),
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

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float."""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int."""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def enrich(self, query: ProcessedQuery) -> ProcessedQuery:
        """Enrich query with computed fields and classifications."""
        if query.mean_time_ms < 10:
            query.tags["performance"] = "excellent"
        elif query.mean_time_ms < 100:
            query.tags["performance"] = "good"
        elif query.mean_time_ms < 1000:
            query.tags["performance"] = "acceptable"
        else:
            query.tags["performance"] = "slow"

        if query.cache_hit_ratio is not None:
            if query.cache_hit_ratio >= 0.95:
                query.tags["cache_efficiency"] = "excellent"
            elif query.cache_hit_ratio > 0.80:
                query.tags["cache_efficiency"] = "good"
            else:
                query.tags["cache_efficiency"] = "poor"

        if query.query_text:
            query_lower = query.query_text.lower()
            if "select" in query_lower:
                query.tags["query_type"] = "read"
            elif any(kw in query_lower for kw in ["insert", "update", "delete"]):
                query.tags["query_type"] = "write"

        if query.mean_time_ms > 1000:
            query.tags["requires_optimization"] = "true"

        if query.calls > 10000:
            query.tags["high_volume"] = "true"

        if query.mean_time_ms and query.stddev_time_ms:
            query.metadata["estimated_p95"] = query.mean_time_ms + (1.645 * query.stddev_time_ms)
            query.metadata["estimated_p99"] = query.mean_time_ms + (2.326 * query.stddev_time_ms)

        return query
