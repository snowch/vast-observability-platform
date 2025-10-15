import pytest
from datetime import datetime
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.models import Event, Metric

def test_logs_processor_normalizes_to_event():
    """Test that the LogsProcessor correctly normalizes a raw log into an Event."""
    processor = LogsProcessor()
    raw_log = {
        "timestamp": "2025-10-14T10:30:00.123Z",
        "source": "postgresql",
        "host": "pg-prod-1",
        "database": "app_db",
        "tags": {"log_level": "warning"},
        "payload": {"event_type": "deadlocks", "count": 5},
    }

    result = processor.normalize(raw_log)

    assert isinstance(result, Event)
    assert result.event_type == 'log'
    assert result.entity_id == "pg-prod-1"
    assert result.source == "postgresql"
    assert result.tags["log_level"] == "warning"
    assert "5 deadlock(s)" in result.message
    assert result.attributes["count"] == 5

def test_queries_processor_normalizes_to_event():
    """Test that the QueriesProcessor correctly normalizes raw query analytics into an Event."""
    processor = QueriesProcessor()
    raw_query = {
        "timestamp": "2025-10-15T12:00:00Z",
        "source": "postgresql",
        "host": "pg-prod-1",
        "database": "app_db",
        "payload": {
            "query": "SELECT * FROM users",
            "calls": 100,
            "mean_time_ms": 15.5,
        },
    }

    result = processor.normalize(raw_query)

    assert isinstance(result, Event)
    assert result.event_type == 'database_query'
    assert result.entity_id == "pg-prod-1"
    assert "executed 100 times" in result.message
    assert result.attributes["mean_time_ms"] == 15.5
    assert "query_hash" in result.attributes

def test_queries_processor_enrichment():
    """Test the enrichment logic for query events."""
    processor = QueriesProcessor()
    raw_slow_query = {
        "timestamp": "2025-10-15T12:00:00Z",
        "source": "postgresql",
        "host": "pg-prod-1",
        "payload": {"query": "SELECT ...", "mean_time_ms": 1500},
    }

    result = processor.process(raw_slow_query, enrich=True)

    assert result.tags["performance"] == "slow"
    
def test_metrics_processor_normalizes_to_metric():
    """Test that the MetricsProcessor correctly normalizes an OTLP payload into Metric objects."""
    processor = MetricsProcessor()
    otlp_payload = {
        "resource": {
            "attributes": [
                {"key": "host.name", "value": {"stringValue": "pg-prod-1"}},
                {"key": "db.system", "value": {"stringValue": "postgresql"}},
            ]
        },
        "scopeMetrics": [{
            "metrics": [{
                "name": "postgresql.backends",
                "gauge": {
                    "dataPoints": [{
                        "timeUnixNano": "1697280000000000000",
                        "asInt": "8"
                    }]
                }
            }]
        }]
    }

    results = processor.normalize(otlp_payload)
    
    assert len(results) == 1
    result = results[0]

    assert isinstance(result, Metric)
    assert result.metric_name == "postgresql.backends"
    assert result.entity_id == "pg-prod-1"
    assert result.metric_value == 8.0
    assert result.metric_type == "gauge"