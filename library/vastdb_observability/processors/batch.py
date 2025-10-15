from typing import Dict, Any, Optional
from vastdb_observability.models import ProcessorBatch, Event, Metric
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.config import ProcessorConfig


class BatchProcessor:
    """Manages batching of processed Events and Metrics for efficient export."""

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()
        self.batch = ProcessorBatch()
        self.metrics_processor = MetricsProcessor(config)
        self.logs_processor = LogsProcessor(config)
        self.queries_processor = QueriesProcessor(config)

    def add(self, message: Dict[str, Any]) -> None:
        """Adds a raw message to the batch after processing it."""
        data_type = message.get("data_type", "")

        try:
            if "scopeMetrics" in message:  # OTLP metrics payload
                processed_metrics = self.metrics_processor.process(message)
                self.batch.metrics.extend(processed_metrics)
            elif data_type == "log":
                processed_event = self.logs_processor.process(message)
                self.batch.events.append(processed_event)
            elif data_type == "query":
                processed_event = self.queries_processor.process(message)
                self.batch.events.append(processed_event)
        except Exception:
            # Optionally log the error
            pass

    def should_flush(self) -> bool:
        """Determines if the current batch should be flushed based on size or age."""
        from datetime import datetime, timedelta

        if self.batch.size() >= self.config.max_batch_size:
            return True
        
        age = datetime.utcnow() - self.batch.created_at
        if age.total_seconds() >= self.config.max_batch_age_seconds:
            return True
            
        return False

    def get_batch(self) -> ProcessorBatch:
        """Returns the current batch and resets it."""
        current_batch = self.batch
        self.batch = ProcessorBatch()
        return current_batch