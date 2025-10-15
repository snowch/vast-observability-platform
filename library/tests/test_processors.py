import pytest
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.logs import LogsProcessor


def test_queries_processor_normalize():
    """Test query normalization."""
    processor = QueriesProcessor()

    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "123",
            "query": "SELECT * FROM users",
            "calls": 100,
            "total_time_ms": 1000.0,
            "mean_time_ms": 10.0,
        },
    }

    result = processor.normalize(raw_query)

    assert result.source == "postgresql"
    assert result.host == "test-host"
    assert result.database_name == "test_db"
    assert result.calls == 100
    assert result.mean_time_ms == 10.0


def test_queries_processor_enrich():
    """Test query enrichment."""
    processor = QueriesProcessor()

    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "123",
            "query": "SELECT * FROM users",
            "calls": 15000,
            "total_time_ms": 150000.0,
            "mean_time_ms": 10.0,
            "cache_hit_ratio": 0.95,
        },
    }

    result = processor.process(raw_query, enrich=True)

    assert result.tags["performance"] == "good"
    assert result.tags["cache_efficiency"] == "excellent"
    assert result.tags["high_volume"] == "true"
    assert result.tags["query_type"] == "read"


def test_logs_processor():
    """Test log processing."""
    processor = LogsProcessor()

    raw_log = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "log",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {"log_level": "warning"},
        "payload": {"event_type": "deadlocks", "count": 5},
    }

    result = processor.process(raw_log)

    assert result.log_level == "warning"
    assert result.event_type == "deadlocks"
    assert "5 deadlock" in result.message
