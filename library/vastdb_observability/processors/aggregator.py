from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from vastdb_observability.models import ProcessedQuery


class Aggregator:
    """Aggregate time-series data into windows."""

    def __init__(self, window_size: str = "5m"):
        """Initialize aggregator with window size (1m, 5m, 15m, 1h, 1d)."""
        self.window_size = self._parse_window_size(window_size)

    def _parse_window_size(self, window: str) -> timedelta:
        """Parse window size string to timedelta."""
        value = int(window[:-1])
        unit = window[-1]

        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return timedelta(minutes=5)

    def _get_window_start(self, timestamp: datetime) -> datetime:
        """Get the start of the time window for a timestamp."""
        epoch = datetime(1970, 1, 1)
        seconds_since_epoch = (timestamp - epoch).total_seconds()
        window_seconds = self.window_size.total_seconds()
        window_number = int(seconds_since_epoch // window_seconds)
        return epoch + timedelta(seconds=window_number * window_seconds)

    def aggregate_queries(self, queries: List[ProcessedQuery]) -> List[Dict[str, Any]]:
        """Aggregate queries into time windows."""
        windows = defaultdict(lambda: defaultdict(list))

        for query in queries:
            window_start = self._get_window_start(query.timestamp)
            key = (window_start, query.query_hash or "unknown", query.host, query.database_name)
            windows[key].append(query)

        aggregated = []
        for (window_start, query_hash, host, database_name), query_list in windows.items():
            total_calls = sum(q.calls for q in query_list)
            total_time = sum(q.total_time_ms for q in query_list)
            mean_times = [q.mean_time_ms for q in query_list]

            aggregated.append({
                "window_start": window_start,
                "window_size": str(self.window_size),
                "query_hash": query_hash,
                "host": host,
                "database_name": database_name,
                "total_calls": total_calls,
                "total_time_ms": total_time,
                "avg_mean_time_ms": sum(mean_times) / len(mean_times),
                "min_mean_time_ms": min(mean_times),
                "max_mean_time_ms": max(mean_times),
                "sample_query": query_list[0].query_text,
            })

        return aggregated
