"""Batch processing example."""
import asyncio
from vastdb_observability import BatchProcessor, VASTExporter
from vastdb_observability.config import ProcessorConfig


async def main():
    # Configure
    config = ProcessorConfig(
        max_batch_size=100,
        max_batch_age_seconds=30,
        enable_enrichment=True,
    )

    # Initialize
    batch_processor = BatchProcessor(config)
    exporter = VASTExporter(
        host="localhost",
        port=5432,
        database="observability",
        username="vast_user",
        password="vast_password",
    )
    await exporter.connect()

    # Simulate processing multiple messages
    messages = [
        {
            "timestamp": "2025-10-14T10:30:00Z",
            "source": "postgresql",
            "data_type": "query",
            "host": "postgres-prod-1",
            "database": "app_db",
            "environment": "production",
            "tags": {},
            "payload": {
                "queryid": f"{i}",
                "query": "SELECT * FROM users",
                "calls": 100,
                "total_time_ms": 1000.0,
                "mean_time_ms": 10.0,
            },
        }
        for i in range(150)
    ]

    for message in messages:
        batch_processor.add(message)

        if batch_processor.should_flush():
            batch = batch_processor.get_batch()
            await exporter.export_batch(batch)
            print(f"Exported batch of {batch.size()} items")

    # Export any remaining
    batch = batch_processor.get_batch()
    if not batch.is_empty():
        await exporter.export_batch(batch)

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
