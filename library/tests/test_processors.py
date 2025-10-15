import pytest
import json
from pathlib import Path
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.models import Event, Metric

# --- Fixture to load sample data ---
@pytest.fixture(scope="module")
def fixture_data():
    """Loads all sample raw data from the fixtures directory."""
    fixture_dir = Path(__file__).parent / "fixtures"
    data = {}
    with open(fixture_dir / "sample-raw-logs.json", "r") as f:
        data["log"] = json.loads(f.readline())
    with open(fixture_dir / "sample-raw-queries.json", "r") as f:
        data["query"] = json.loads(f.readline())
    with open(fixture_dir / "sample-otel-metrics.json", "r") as f:
        data["metric"] = json.load(f)[0]
    return data

# --- New test that would have caught the bug ---
def test_metrics_processor_handles_fixture_data(fixture_data):
    """
    This is the crucial test that catches the bug.
    It uses the actual fixture file and asserts that the processor
    returns a non-empty list, preventing the IndexError.
    """
    processor = MetricsProcessor()
    raw_metric_data = fixture_data["metric"]
    
    # Process the data from the file
    results = processor.normalize(raw_metric_data)
    
    # Assert that the processor actually produced results
    assert results, "MetricsProcessor should produce at least one metric from the fixture data"
    assert isinstance(results[0], Metric)
    assert results[0].metric_name == "postgresql.blocks_read"
    assert results[0].metric_value == 12345.0
    assert results[0].entity_id == "postgres"

# --- Existing tests, updated for clarity ---
def test_logs_processor_normalizes_to_event(fixture_data):
    """Test that the LogsProcessor correctly normalizes a raw log into an Event."""
    processor = LogsProcessor()
    result = processor.normalize(fixture_data["log"])

    assert isinstance(result, Event)
    assert result.event_type == 'log'
    assert result.entity_id == "postgres"
    assert "active connections" in result.message

def test_queries_processor_normalizes_to_event(fixture_data):
    """Test that the QueriesProcessor correctly normalizes raw query analytics into an Event."""
    processor = QueriesProcessor()
    result = processor.normalize(fixture_data["query"])

    assert isinstance(result, Event)
    assert result.event_type == 'database_query'
    assert result.entity_id == "postgres"
    assert "executed 12 times" in result.message
    assert result.attributes["mean_time_ms"] == 1533.320280416667