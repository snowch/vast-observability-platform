"""Simple usage example for vastdb-observability library."""
import asyncio
from vastdb_observability import QueriesProcessor, VASTExporter


async def main():
    # Initialize processor
    processor = QueriesProcessor()

    # Initialize exporter
    exporter = VASTExporter(
        host="localhost",
        port=5432,
        database="observability",
        username="vast_user",
        password="vast_password",
    )
    await exporter.connect()

    # Simulate raw query data
    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "postgres-prod-1",
        "database": "app_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "1234567890",
            "query": "SELECT * FROM users WHERE id = $1",
            "calls": 1523,
            "total_time_ms": 45123.45,
            "mean_time_ms": 29.63,
        },
    }

    # Process
    processed = processor.process(raw_query, enrich=True)

    print(f"Processed query: {processed.query_text}")
    print(f"Performance: {processed.tags.get('performance')}")
    print(f"Query hash: {processed.query_hash}")

    # Export
    await exporter.export_queries([processed])
    print("✓ Exported to VAST Database")

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
