"""
vastdb-observability - A Python library for processing and exporting 
observability telemetry to VAST Database using an extensible, entity-centric model.
"""
__version__ = "2.0.0"

# Import processors
from vastdb_observability.processors.metrics import MetricsProcessor
from vastdb_observability.processors.logs import LogsProcessor
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.batch import BatchProcessor
from vastdb_observability.processors.aggregator import Aggregator

# Import the main exporter
from vastdb_observability.exporters.vast import VASTExporter

# Import the new, extensible models
from vastdb_observability.models import (
    Event,
    Metric,
    Entity,
    ProcessorBatch,
)

# Define the public API for the library
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