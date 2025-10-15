#!/usr/bin/env python3
 
"""
A usage example for the vastdb-observability library that reads raw
telemetry data from the sample fixture files.

This script demonstrates a more realistic workflow:
1. Load raw data for logs, queries, and metrics from JSON files.
2. Process each type of data into the unified, extensible models.
3. Export the processed data to VAST Database.
"""
import asyncio
import json
from pathlib import Path
from vastdb_observability import (
    LogsProcessor, 
    QueriesProcessor, 
    MetricsProcessor, 
    VASTExporter
)
from vastdb_observability.config import ProcessorConfig


def load_fixture_data():
    """Loads sample raw data from the test fixture JSON files."""
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    
    # The logs and queries files are JSON Lines format (one JSON object per line)
    # We'll just read the first line for this example.
    with open(fixture_dir / "sample-raw-logs.json", "r") as f:
        raw_log = json.loads(f.readline())
        
    with open(fixture_dir / "sample-raw-queries.json", "r") as f:
        raw_query = json.loads(f.readline())
        
    # The metrics file is a standard JSON array
    with open(fixture_dir / "sample-otel-metrics.json", "r") as f:
        # The file contains a list of resource metrics, we'll use the first one
        raw_metric_otlp = json.load(f)[0]
        
    return raw_log, raw_query, raw_metric_otlp


async def main():
    """
    Processes one of each telemetry type from fixture files and exports them
    to their respective tables in VAST Database.
    """
    # 1. Load configuration from environment variables or a .env file
    config = ProcessorConfig()

    # 2. Initialize the processors for each data type
    logs_processor = LogsProcessor()
    queries_processor = QueriesProcessor()
    metrics_processor = MetricsProcessor()

    # 3. Initialize the VAST Exporter
    exporter = VASTExporter(
        endpoint=config.vast_endpoint,
        access_key=config.vast_access_key,
        secret_key=config.vast_secret_key,
        bucket_name=config.vast_bucket,
        schema_name=config.vast_schema
    )
    await exporter.connect()
    print(f"✓ Connected to VAST DB at {config.vast_endpoint}")
    print("-" * 40)

    # 4. Load the raw telemetry data from the fixture files
    print("Loading raw data from tests/fixtures/...")
    raw_log, raw_query, raw_metric_otlp = load_fixture_data()
    print("✓ Data loaded successfully.")
    print("-" * 40)

    # 5. Process each piece of raw data into the unified models
    processed_log_event = logs_processor.process(raw_log)
    print("Processed Log as Event:")
    print(f"  Entity: {processed_log_event.entity_id}, Message: {processed_log_event.message}")

    processed_query_event = queries_processor.process(raw_query)
    print("Processed Query as Event:")
    print(f"  Entity: {processed_query_event.entity_id}, Message: {processed_query_event.message}")

    processed_metrics = metrics_processor.process(raw_metric_otlp)
    print("Processed OTLP data as Metric:")
    print(f"  Entity: {processed_metrics[0].entity_id}, Metric: {processed_metrics[0].metric_name}, Value: {processed_metrics[0].metric_value}")
    print("-" * 40)
    
    # 6. Export the processed data to the appropriate tables in VAST DB
    all_events = [processed_log_event, processed_query_event]
    
    await exporter.export_events(all_events)
    print(f"✓ Exported {len(all_events)} events to the 'events' table.")
    
    await exporter.export_metrics(processed_metrics)
    print(f"✓ Exported {len(processed_metrics)} metrics to the 'metrics' table.")

    await exporter.disconnect()
    print("\n✓ Export complete and connection closed.")


if __name__ == "__main__":
    asyncio.run(main())