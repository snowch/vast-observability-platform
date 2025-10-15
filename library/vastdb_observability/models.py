"""
Defines the core, extensible data models for the observability platform.
- Event: A unified model for any time-series event (logs, spans, queries).
- Metric: A model for all numeric, time-series measurements, linked to an entity.
- Entity: Stores metadata about the systems being monitored.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid
import hashlib


class Event(BaseModel):
    """A unified model for any time-series event (e.g., log, span, query)."""
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    entity_id: str  # The unique ID of the source entity (e.g., hostname, service name)
    event_type: str # A specific type for the event (e.g., 'log', 'span', 'mongo_slow_query')
    source: str     # The system type that generated the event (e.g., 'postgresql', 'cisco_ios', 'linux')
    environment: str = "production"
    message: str    # A human-readable summary of the event
    tags: Dict[str, str] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict) # Detailed, schemaless payload
    trace_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Metric(BaseModel):
    """A generic model for any numeric, time-series measurement."""
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    entity_id: str  # The unique ID of the source entity
    metric_name: str
    metric_value: float
    metric_type: Literal["gauge", "counter", "histogram"]
    source: str
    environment: str = "production"
    unit: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    """Stores metadata about a monitored entity (e.g., a host, database, switch)."""
    model_config = ConfigDict(coerce_numbers_to_str=True)

    entity_id: str      # Unique identifier (e.g., hostname, serial number)
    entity_type: str    # e.g., 'host', 'database', 'switch', 'pod'
    first_seen: datetime
    last_seen: datetime
    attributes: Dict[str, Any] = Field(default_factory=dict) # IPs, OS version, k8s labels


class ProcessorBatch(BaseModel):
    """A batch of processed data ready for export."""

    events: List[Event] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_empty(self) -> bool:
        """Check if the batch contains any data."""
        return not (self.events or self.metrics)

    def size(self) -> int:
        """Return the total number of items in the batch."""
        return len(self.events) + len(self.metrics)