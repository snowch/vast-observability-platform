from datetime import datetime
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid
import hashlib


class ProcessedMetric(BaseModel):
    """Normalized metric data for VAST Database."""
    
    # Pydantic v2 automatically serializes datetime to ISO format
    model_config = ConfigDict()

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    source: str
    host: str
    database_name: str
    environment: str = "production"
    metric_name: str
    metric_value: float
    metric_type: Literal["gauge", "counter", "histogram"]
    unit: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessedLog(BaseModel):
    """Normalized log data for VAST Database."""
    
    # Pydantic v2 automatically serializes datetime to ISO format
    model_config = ConfigDict()

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    source: str
    host: str
    database_name: str
    environment: str = "production"
    log_level: str = "info"
    event_type: str
    message: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessedQuery(BaseModel):
    """Normalized query data for VAST Database."""
    
    # Pydantic v2 automatically serializes datetime to ISO format
    model_config = ConfigDict()

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    source: str
    host: str
    database_name: str
    environment: str = "production"
    query_id: str
    query_text: Optional[str] = None
    query_hash: Optional[str] = None
    calls: int = 0
    total_time_ms: float = 0.0
    mean_time_ms: float = 0.0
    min_time_ms: Optional[float] = None
    max_time_ms: Optional[float] = None
    stddev_time_ms: Optional[float] = None
    rows_affected: Optional[int] = None
    cache_hit_ratio: Optional[float] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def compute_query_hash(query_text: str) -> str:
        """Compute a hash of the normalized query for grouping."""
        normalized = " ".join(query_text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]


class ProcessorBatch(BaseModel):
    """A batch of processed data ready for export."""

    metrics: List[ProcessedMetric] = Field(default_factory=list)
    logs: List[ProcessedLog] = Field(default_factory=list)
    queries: List[ProcessedQuery] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_empty(self) -> bool:
        """Check if batch contains any data."""
        return not (self.metrics or self.logs or self.queries)

    def size(self) -> int:
        """Total number of items in batch."""
        return len(self.metrics) + len(self.logs) + len(self.queries)