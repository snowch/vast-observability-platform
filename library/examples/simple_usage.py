"""
A usage example for the vastdb-observability library that reads raw
telemetry data from the sample fixture files and exports the processed
data, including the corresponding entity.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from vastdb_observability import (
    LogsProcessor, 
    QueriesProcessor, 
    MetricsProcessor, 
    VASTExporter,
    Entity  # Import the Entity model
)
from vastdb_observability.config import ProcessorConfig


def load_fixture_data():
    """Loads sample raw data from the test fixture JSON files."""
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    
    with open(fixture_dir / "sample-raw-logs.json", "r") as f:
        raw_log = json.loads(f.readline())
        
    with open(fixture_dir / "sample-raw-queries.json", "r") as f:
        raw_query = json.loads(f.readline())
        
    with open(fixture_dir / "sample-otel-metrics.json", "r") as f:
        raw_metric_otlp = json.load(f)[0]
        
    return raw_log, raw_query, raw_metric_otlp


async def main():
    """
    Processes telemetry from fixtures, creates an associated entity, and exports all data.
    """
    config = ProcessorConfig()
    logs_processor, queries_processor, metrics_processor = LogsProcessor(), QueriesProcessor(), MetricsProcessor()

    exporter = VASTExporter(
        endpoint=config.vast_endpoint, access_key=config.vast_access_key,
        secret_key=config.vast_secret_key, bucket_name=config.vast_bucket
    )
    await exporter.connect()
    print(f"✓ Connected to VAST DB at {config.vast_endpoint}")
    print("-" * 40)

    print("Loading raw data from tests/fixtures/...")
    raw_log, raw_query, raw_metric_otlp = load_fixture_data()
    print("✓ Data loaded successfully.")
    print("-" * 40)

    # Process all raw data
    processed_log_event = logs_processor.process(raw_log)
    processed_query_event = queries_processor.process(raw_query)
    processed_metrics = metrics_processor.process(raw_metric_otlp)
    
    # *** NEW: Create the Entity ***
    # In a real application, you'd check if this entity already exists.
    # Here, we create an Entity object based on the data we just processed.
    entity_id = processed_log_event.entity_id  # All our data comes from the 'postgres' host
    now = datetime.utcnow()
    
    entity_to_export = Entity(
        entity_id=entity_id,
        entity_type="database_host",  # Classify the entity
        first_seen=now,
        last_seen=now,
        attributes={
            "source_system": "postgresql",
            "environment": "development",
            "ip_address": "172.18.0.2" # Example metadata
        }
    )
    
    print("Processed Log as Event:    ", f"Entity: {processed_log_event.entity_id}, Message: {processed_log_event.message}")
    print("Processed Query as Event:  ", f"Entity: {processed_query_event.entity_id}, Message: {processed_query_event.message}")
    print("Processed OTLP as Metric:  ", f"Entity: {processed_metrics[0].entity_id}, Name: {processed_metrics[0].metric_name}, Value: {processed_metrics[0].metric_value}")
    print("Created Entity:            ", f"ID: {entity_to_export.entity_id}, Type: {entity_to_export.entity_type}")
    print("-" * 40)
    
    # Export all processed data types
    all_events = [processed_log_event, processed_query_event]
    
    await exporter.export_events(all_events)
    print(f"✓ Exported {len(all_events)} events to the 'events' table.")
    
    await exporter.export_metrics(processed_metrics)
    print(f"✓ Exported {len(processed_metrics)} metrics to the 'metrics' table.")

    await exporter.export_entities([entity_to_export])
    print(f"✓ Exported 1 entity to the 'entities' table.")

    await exporter.disconnect()
    print("\n✓ Export complete and connection closed.")


if __name__ == "__main__":
    asyncio.run(main())