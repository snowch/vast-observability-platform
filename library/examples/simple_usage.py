"""A simple usage example for the vastdb-observability library with the new schema."""
import asyncio
from vastdb_observability import QueriesProcessor, VASTExporter
from vastdb_observability.config import ProcessorConfig

async def main():
    # Load configuration from environment or .env file
    config = ProcessorConfig()

    # Initialize the processor for query data
    processor = QueriesProcessor()

    # Initialize the exporter with VAST DB connection details
    exporter = VASTExporter(
        endpoint=config.vast_endpoint,
        access_key=config.vast_access_key,
        secret_key=config.vast_secret_key,
        bucket_name=config.vast_bucket,
        schema_name=config.vast_schema
    )
    await exporter.connect()

    # Simulate raw query data coming from a collector
    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "postgres-prod-1",
        "database": "app_db",
        "payload": {
            "queryid": "1234567890",
            "query": "SELECT * FROM users WHERE id = $1",
            "calls": 1523,
            "mean_time_ms": 29.63,
        },
    }

    # Process the raw data into a structured Event object
    processed_event = processor.process(raw_query, enrich=True)

    print(f"Processed Event Type: {processed_event.event_type}")
    print(f"Entity: {processed_event.entity_id}")
    print(f"Message: {processed_event.message}")
    print(f"Performance Tag: {processed_event.tags.get('performance')}")

    # Export the processed event to the 'events' table in VAST Database
    await exporter.export_events([processed_event])
    print("\n✓ Exported event to VAST Database")

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())