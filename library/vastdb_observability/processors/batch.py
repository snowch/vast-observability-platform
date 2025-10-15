from typing import Dict, Any, Optional
from datetime import datetime
from vastdb_observability.models import ProcessorBatch
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.config import ProcessorConfig


class BatchProcessor:
    """Batch processor for efficient bulk operations."""

    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()
        self.batch = ProcessorBatch()
        self.metrics_processor = MetricsProcessor(config)
        self.logs_processor = LogsProcessor(config)
        self.queries_processor = QueriesProcessor(config)

    def add(self, message: Dict[str, Any]) -> None:
        """Add a message to the batch."""
        data_type = message.get("data_type", "")

        if data_type == "log":
            processed = self.logs_processor.process(message)
            self.batch.logs.append(processed)
        elif data_type == "query":
            processed = self.queries_processor.process(message)
            self.batch.queries.append(processed)
        elif "scopeMetrics" in message:
            processed = self.metrics_processor.process(message)
            self.batch.metrics.extend(processed)

    def should_flush(self) -> bool:
        """Check if batch should be flushed."""
        if self.batch.size() >= self.config.max_batch_size:
            return True

        age = datetime.utcnow() - self.batch.created_at
        if age.total_seconds() >= self.config.max_batch_age_seconds:
            return True

        return False

    def get_batch(self) -> ProcessorBatch:
        """Get current batch and reset."""
        current = self.batch
        self.batch = ProcessorBatch()
        return current
