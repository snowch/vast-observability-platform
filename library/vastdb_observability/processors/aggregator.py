"""
Aggregates time-series data into windows.
Updated to use the generic Event model for query aggregation.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from vastdb_observability.models import Event


class Aggregator:
    """Aggregates time-series data, such as query events, into time windows."""

    def __init__(self, window_size: str = "5m"):
        """Initializes the aggregator with a specified window size (e.g., '1m', '5m', '1h')."""
        self.window_size = self._parse_window_size(window_size)

    def _parse_window_size(self, window: str) -> timedelta:
        """Parses a window size string into a timedelta object."""
        value = int(window[:-1])
        unit = window[-1]

        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            # Default to 5 minutes if format is unrecognized
            return timedelta(minutes=5)

    def _get_window_start(self, timestamp: datetime) -> datetime:
        """Calculates the start of the time window for a given timestamp."""
        epoch = datetime(1970, 1, 1)
        seconds_since_epoch = (timestamp - epoch).total_seconds()
        window_seconds = self.window_size.total_seconds()
        window_number = int(seconds_since_epoch // window_seconds)
        return epoch + timedelta(seconds=window_number * window_seconds)

    def aggregate_query_events(self, events: List[Event]) -> List[Dict[str, Any]]:
        """Aggregates a list of query events into time windows."""
        windows = defaultdict(list)

        # Filter for query events and group them by a composite key
        for event in events:
            if event.event_type == 'database_query':
                window_start = self._get_window_start(event.timestamp)
                query_hash = event.attributes.get("query_hash", "unknown")
                key = (window_start, query_hash, event.entity_id, event.source)
                windows[key].append(event)

        aggregated_results = []
        for (window_start, query_hash, entity_id, source), event_list in windows.items():
            # Sum and average the relevant metrics from the attributes payload
            total_calls = sum(e.attributes.get("calls", 0) for e in event_list)
            total_time = sum(e.attributes.get("total_time_ms", 0.0) for e in event_list)
            mean_times = [e.attributes.get("mean_time_ms", 0.0) for e in event_list]

            if not mean_times: continue

            aggregated_results.append({
                "window_start": window_start,
                "window_size_minutes": self.window_size.total_seconds() / 60,
                "entity_id": entity_id,
                "source": source,
                "query_hash": query_hash,
                "total_calls": total_calls,
                "total_time_ms": total_time,
                "avg_mean_time_ms": sum(mean_times) / len(mean_times),
                "min_mean_time_ms": min(mean_times),
                "max_mean_time_ms": max(mean_times),
                "sample_query": event_list[0].attributes.get("query", "N/A"),
            })

        return aggregated_results