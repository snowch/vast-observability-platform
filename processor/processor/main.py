import asyncio
import json
import signal
import sys
import time
import gzip
from confluent_kafka import Consumer, KafkaError
import structlog
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest

from vastdb_observability import BatchProcessor, VASTExporter
from .config import Settings

logger = structlog.get_logger()

class KafkaProcessorService:
    def __init__(self):
        self.settings = Settings()
        self.running = True
        self.consumer = None
        self.batch_processor = None
        self.exporter = None

    async def initialize(self):
        """Initializes all components of the service."""
        logger.info("initializing_processor_service")

        # Configure Kafka consumer
        consumer_conf = {
            'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': self.settings.KAFA_GROUP_ID,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        self.consumer = Consumer(consumer_conf)
        self.consumer.subscribe(self.settings.KAFKA_TOPICS.split(','))
        logger.info("kafka_consumer_subscribed", topics=self.settings.KAFKA_TOPICS)

        # Initialize the batch processor from the library
        self.batch_processor = BatchProcessor(config=self.settings)

        # Initialize the VAST exporter
        self.exporter = VASTExporter(
            endpoint=self.settings.VAST_ENDPOINT,
            access_key=self.settings.VAST_ACCESS_KEY,
            secret_key=self.settings.VAST_SECRET_KEY,
            bucket_name=self.settings.VAST_BUCKET
        )
        await self.exporter.connect()
        logger.info("vast_exporter_connected")

    def consume_loop(self):
        """The main loop to consume messages from Kafka."""
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # No message received within timeout
                    if self.batch_processor.should_flush():
                        asyncio.run(self.flush_batch())
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error("kafka_consumer_error", error=msg.error())
                        break

                # Process the message
                try:
                    topic = msg.topic()
                    value = msg.value()
                    
                    if topic == 'otel-metrics':
                        # Decompress the gzipped data
                        decompressed_data = gzip.decompress(value)
                        
                        # Parse the Protobuf message
                        metrics_request = ExportMetricsServiceRequest()
                        metrics_request.ParseFromString(decompressed_data)
                        
                        # Convert to Dict for the processor
                        message_data = MessageToDict(metrics_request.resource_metrics[0])
                    else:
                        # Handle JSON messages for other topics
                        message_data = json.loads(value.decode('utf-8'))

                    self.batch_processor.add(message_data)
                    self.consumer.commit(asynchronous=True)
                except (json.JSONDecodeError, gzip.BadGzipFile, Exception) as e:
                    logger.error("message_processing_failed", error=str(e), topic=msg.topic())

                # Check if batch should be flushed
                if self.batch_processor.should_flush():
                    asyncio.run(self.flush_batch())

        finally:
            self.consumer.close()


    async def flush_batch(self):
        """Flushes the current batch to VAST DB."""
        batch = self.batch_processor.get_batch()
        if not batch.is_empty():
            logger.info("flushing_batch", size=batch.size())
            await self.exporter.export_batch(batch)
            logger.info("batch_flushed_successfully")

    async def shutdown(self):
        """Shuts down the service gracefully."""
        self.running = False
        logger.info("shutting_down_processor")
        if self.exporter:
            # Flush any remaining items before shutting down
            await self.flush_batch()
            await self.exporter.disconnect()
        logger.info("processor_shutdown_complete")

def main():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )

    service = KafkaProcessorService()
    loop = asyncio.get_event_loop()

    def handle_signal(sig):
        logger.info(f"received_signal_{sig},_shutting_down")
        loop.create_task(service.shutdown())

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(service.initialize())
        service.consume_loop()
    except Exception as e:
        logger.error("service_startup_failed", error=str(e))
    finally:
        logger.info("service_terminated")

if __name__ == "__main__":
    main()