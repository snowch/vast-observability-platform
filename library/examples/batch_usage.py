"""An example of batch processing with the vastdb-observability library."""
import asyncio
from vastdb_observability import BatchProcessor, VASTExporter
from vastdb_observability.config import ProcessorConfig

async def main():
    # Load configuration, customizing batch settings
    config = ProcessorConfig(
        max_batch_size=50,
        max_batch_age_seconds=10,
        enable_enrichment=True,
    )

    # Initialize the batch processor and exporter
    batch_processor = BatchProcessor(config)
    exporter = VASTExporter(
        endpoint=config.vast_endpoint,
        access_key=config.vast_access_key,
        secret_key=config.vast_secret_key,
        bucket_name=config.vast_bucket,
    )
    await exporter.connect()

    # Simulate a stream of raw log and query messages
    messages = []
    for i in range(120):
        if i % 2 == 0:
            messages.append({
                "timestamp": f"2025-10-14T10:30:{i//2:02d}Z", "source": "postgresql",
                "data_type": "query", "host": f"pg-prod-{i%3}",
                "payload": {"query": f"SELECT {i}", "calls": 1, "mean_time_ms": i * 10},
            })
        else:
            messages.append({
                "timestamp": f"2025-10-14T10:30:{i//2:02d}Z", "source": "postgresql",
                "data_type": "log", "host": f"pg-prod-{i%3}", "tags": {"log_level": "info"},
                "payload": {"event_type": "connection_stats", "active": i, "total": 20},
            })

    # Process messages, flushing batches as they become ready
    for message in messages:
        batch_processor.add(message)

        if batch_processor.should_flush():
            batch = batch_processor.get_batch()
            await exporter.export_batch(batch)
            print(f"Exported batch of {batch.size()} items (events: {len(batch.events)}, metrics: {len(batch.metrics)})")

    # Export any remaining items after the loop
    final_batch = batch_processor.get_batch()
    if not final_batch.is_empty():
        await exporter.export_batch(final_batch)
        print(f"Exported final batch of {final_batch.size()} items.")

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())