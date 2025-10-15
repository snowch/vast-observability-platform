"""Processor modules for data normalization and enrichment."""

from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.batch import BatchProcessor
from vastdb_observability.processors.aggregator import Aggregator

__all__ = [
    "MetricsProcessor",
    "LogsProcessor",
    "QueriesProcessor",
    "BatchProcessor",
    "Aggregator",
]
