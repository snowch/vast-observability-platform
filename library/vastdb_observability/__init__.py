"""
vastdb-observability - Database observability telemetry processing library.
"""
__version__ = "1.0.0"

from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.batch import BatchProcessor
from vastdb_observability.processors.aggregator import Aggregator
from vastdb_observability.exporters.vast import VASTExporter
from vastdb_observability.models import (
    ProcessedMetric,
    ProcessedLog,
    ProcessedQuery,
    ProcessorBatch,
)

__all__ = [
    "MetricsProcessor",
    "LogsProcessor",
    "QueriesProcessor",
    "BatchProcessor",
    "Aggregator",
    "VASTExporter",
    "ProcessedMetric",
    "ProcessedLog",
    "ProcessedQuery",
    "ProcessorBatch",
]
