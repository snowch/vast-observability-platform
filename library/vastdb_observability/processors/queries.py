from typing import Dict, Any, Optional
from datetime import datetime
from vastdb_observability.models import Event
from vastdb_observability.processors.base import BaseProcessor
import hashlib


class QueriesProcessor(BaseProcessor[Event]):
    """Processes raw query analytics into the unified Event model."""

    def normalize(self, raw_query: Dict[str, Any]) -> Event:
        """Normalizes a raw query dictionary into a structured Event."""
        payload = raw_query.get("payload", {})
        query_text = payload.get("query", "")
        
        # Add a query hash to the payload for easier grouping
        if query_text:
            payload["query_hash"] = self._compute_query_hash(query_text)

        return Event(
            timestamp=self._parse_timestamp(raw_query.get("timestamp")),
            entity_id=raw_query.get("host", "unknown"),
            event_type='database_query',  # A specific event type for queries
            source=raw_query.get("source", "unknown"),
            environment=raw_query.get("environment", "production"),
            message=f"Query executed {payload.get('calls', 0)} times with avg latency {payload.get('mean_time_ms', 0):.2f}ms.",
            tags=raw_query.get("tags", {}),
            attributes=payload,  # Store all performance details in the attributes field
        )

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Safely parses a timestamp string into a datetime object."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        if isinstance(timestamp_str, str):
            try:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return datetime.utcnow()
        return datetime.utcnow()

    def _compute_query_hash(self, query_text: str) -> str:
        """Computes a consistent hash of the normalized query text."""
        normalized = " ".join(query_text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def enrich(self, event: Event) -> Event:
        """Enriches the query event with performance and type classifications."""
        mean_time = event.attributes.get('mean_time_ms', 0.0)
        
        if mean_time > 1000:
            event.tags['performance'] = 'slow'
        elif mean_time > 100:
            event.tags['performance'] = 'acceptable'
        else:
            event.tags['performance'] = 'good'
            
        query_text = event.attributes.get("query", "").lower()
        if "select" in query_text:
            event.tags["query_type"] = "read"
        elif any(kw in query_text for kw in ["insert", "update", "delete"]):
            event.tags["query_type"] = "write"
            
        return event