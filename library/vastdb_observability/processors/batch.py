"""
Core component for processing and batching raw telemetry data.

This module provides the `BatchProcessor`, which acts as the primary
entry point for a consumer service (like the main Kafka processor). It holds
instances of the specialized processors (Metrics, Logs, Queries) and routes
incoming raw messages to the correct one based on the Kafka topic or
message content.

It collects the processed, normalized data (Events and Metrics) into a
`ProcessorBatch` object. This batch can then be flushed to an exporter when it
reaches a configured size or age.
"""
from typing import Dict, Any, Optional
import structlog
from vastdb_observability.models import ProcessorBatch, Event, Metric
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.config import ProcessorConfig

logger = structlog.get_logger()

class BatchProcessor:
    """
    Manages the processing and batching of raw Events and Metrics.

    This class orchestrates the normalization and enrichment pipeline.
    A service (e.g., a Kafka consumer) should create a single instance of
    `BatchProcessor`. For each raw message received, the service calls `add()`.
    The service should then periodically call `should_flush()` to check if the
    batch is ready, and if so, call `get_batch()` to retrieve the data
    for export.

    Attributes:
        config (ProcessorConfig): Configuration object for batch settings.
        batch (ProcessorBatch): The current in-memory batch of processed data.
        metrics_processor (MetricsProcessor): Processor for OTLP metrics.
        logs_processor (LogsProcessor): Processor for log data.
        queries_processor (QueriesProcessor): Processor for query analytics data.
    """

    def __init__(self, config: Optional[ProcessorConfig] = None):
        """
        Initializes the BatchProcessor and its sub-processors.

        Args:
            config: A ProcessorConfig object. If None, default settings
                    are loaded from environment variables or .env file.
        """
        self.config = config or ProcessorConfig()
        self.batch = ProcessorBatch()
        self.metrics_processor = MetricsProcessor(self.config)
        self.logs_processor = LogsProcessor(self.config)
        self.queries_processor = QueriesProcessor(self.config)

    def add(self, message: Dict[str, Any], topic: str = "") -> None:
        """
        Processes a single raw message and adds the result to the batch.

        This method inspects the Kafka topic (if provided) or the message
        content to determine the data type. It then delegates the
        normalization and enrichment to the appropriate sub-processor
        (Metrics, Logs, or Queries).

        The resulting `Event` or `Metric` object(s) are appended to the
        internal batch.

        The fallback logic (checking `data_type` or `scope_metrics`) ensures
        compatibility with data sources that may not provide a topic name.

        Args:
            message: The raw data, typically a dictionary decoded from JSON.
            topic: The Kafka topic the message came from (e.g., 'raw-logs').
                   This is the preferred method for routing.
        """
        try:
            if topic == 'otel-metrics':
                processed_metrics = self.metrics_processor.process(message, topic=topic)
                self.batch.metrics.extend(processed_metrics)
            elif topic == 'raw-logs' or topic == 'raw-host-logs':
                processed_event = self.logs_processor.process(message, topic=topic)
                self.batch.events.append(processed_event)
            elif topic == 'raw-queries':
                processed_event = self.queries_processor.process(message, topic=topic)
                self.batch.events.append(processed_event)
            
            # --- Fallback logic if topic is not provided ---
            elif "scope_metrics" in message:
                 processed_metrics = self.metrics_processor.process(message)
                 self.batch.metrics.extend(processed_metrics)
            elif message.get("data_type") == "log":
                processed_event = self.logs_processor.process(message)
                self.batch.events.append(processed_event)
            elif message.get("data_type") == "query":
                processed_event = self.queries_processor.process(message)
                self.batch.events.append(processed_event)
        except Exception as e:
            logger.error("batch_add_failed", topic=topic, error=str(e), message_sample=str(message)[:200])


    def should_flush(self) -> bool:
        """
        Checks if the current batch meets the criteria for flushing.

        A batch should be flushed if:
        1. The total number of items (Events + Metrics) has reached
           the `max_batch_size`.
        2. The age of the batch (time since it was created) has reached
           the `max_batch_age_seconds`.

        Returns:
            bool: True if the batch should be flushed, False otherwise.
        """
        from datetime import datetime, timedelta

        if self.batch.size() >= self.config.max_batch_size:
            logger.debug("batch_flush_triggered_by_size", size=self.batch.size())
            return True
        
        age = datetime.utcnow() - self.batch.created_at
        if age.total_seconds() >= self.config.max_batch_age_seconds:
            logger.debug("batch_flush_triggered_by_age", age_seconds=age.total_seconds())
            return True
            
        return False

    def get_batch(self) -> ProcessorBatch:
        """
        Retrieves the current batch and atomically resets the internal batch.

        This method is designed to be called after `should_flush()` returns True.
        It returns the populated batch for export and immediately replaces it
        with a new, empty `ProcessorBatch` so that new messages can be
        collected without data loss.

        Returns:
            ProcessorBatch: The batch containing all collected Event and Metric
                            objects since the last flush.
        """
        current_batch = self.batch
        self.batch = ProcessorBatch()
        return current_batch