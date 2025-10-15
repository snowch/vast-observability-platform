"""
vastdb-observability - A Python library for processing and exporting 
observability telemetry to VAST Database using an extensible, entity-centric model.
"""
__version__ = "2.0.0"

from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.batch import BatchProcessor
from vastdb_observability.processors.aggregator import Aggregator
from vastdb_observability.exporters.vast import VASTExporter
from vastdb_observability.models import (
    Event,
    Metric,
    Entity,
    ProcessorBatch,
)

__all__ = [
    # Processors
    "MetricsProcessor",
    "LogsProcessor",
    "QueriesProcessor",
    "BatchProcessor",
    "Aggregator",
    
    # Exporter
    "VASTExporter",
    
    # Core Models
    "Event",
    "Metric",
    "Entity",
    "ProcessorBatch",
]