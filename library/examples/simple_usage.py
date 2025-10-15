"""
A simple usage example for the vastdb-observability library, demonstrating how
to process and export multiple types of telemetry (logs, queries, and metrics)
using the new, extensible, entity-centric schema.
"""
import asyncio
from vastdb_observability import (
    LogsProcessor, 
    QueriesProcessor, 
    MetricsProcessor, 
    VASTExporter
)
from vastdb_observability.config import ProcessorConfig

async def main():
    """
    Processes one of each telemetry type (log, query, metric) and exports them
    to their respective tables in VAST Database.
    """
    # 1. Load configuration from environment or .env file
    config = ProcessorConfig()

    # 2. Initialize all necessary processors
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

    # 4. Simulate different types of raw telemetry data
    
    # A raw log about database deadlocks
    raw_log = {
        "timestamp": "2025-10-15T14:30:00.123Z",
        "source": "postgresql",
        "data_type": "log",
        "host": "pg-prod-A1",
        "tags": {"log_level": "warning"},
        "payload": {"event_type": "deadlocks", "count": 3, "details": "..."},
    }

    # Raw query analytics for a slow query
    raw_query = {
        "timestamp": "2025-10-15T14:30:05.456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "pg-prod-A1",
        "payload": {
            "query": "SELECT ... FROM orders JOIN customers ...",
            "calls": 50,
            "mean_time_ms": 1250.7,
        },
    }

    # A raw OTLP metric for CPU utilization
    raw_metric_otlp = {
        "resource": { "attributes": [ {"key": "host.name", "value": {"stringValue": "pg-prod-A1"}}, {"key": "db.system", "value": {"stringValue": "postgresql"}} ] },
        "scopeMetrics": [{
            "metrics": [{
                "name": "system.cpu.utilization", "unit": "%",
                "gauge": { "dataPoints": [{ "timeUnixNano": "1697376610000000000", "asDouble": "0.85" }] }
            }]
        }]
    }

    # 5. Process each piece of raw data
    
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
    
    # 6. Export the processed data to VAST DB
    
    # Combine log and query events into one list
    all_events = [processed_log_event, processed_query_event]
    
    await exporter.export_events(all_events)
    print(f"✓ Exported {len(all_events)} events to the 'events' table.")
    
    await exporter.export_metrics(processed_metrics)
    print(f"✓ Exported {len(processed_metrics)} metrics to the 'metrics' table.")

    await exporter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())