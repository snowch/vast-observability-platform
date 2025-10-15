#!/bin/bash

# ============================================================================
# vastdb-observability Project Setup Script
# ============================================================================
# This script creates the complete project structure with all files.
# Usage: ./setup.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project name
PROJECT_NAME="vastdb-observability"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  vastdb-observability Project Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if directory exists
if [ -d "$PROJECT_NAME" ]; then
    echo -e "${YELLOW}Warning: Directory '$PROJECT_NAME' already exists.${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
    rm -rf "$PROJECT_NAME"
fi

# Create project directory
echo -e "${GREEN}Creating project directory...${NC}"
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# ============================================================================
# Create Directory Structure
# ============================================================================
echo -e "${GREEN}Creating directory structure...${NC}"

mkdir -p vastdb_observability/processors
mkdir -p vastdb_observability/exporters
mkdir -p tests
mkdir -p examples
mkdir -p docs

# ============================================================================
# Create Python Package Files
# ============================================================================
echo -e "${GREEN}Creating Python package files...${NC}"

# vastdb_observability/__init__.py
cat > vastdb_observability/__init__.py << 'EOF'
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
EOF

# vastdb_observability/config.py
cat > vastdb_observability/config.py << 'EOF'
from pydantic_settings import BaseSettings
from typing import Optional


class ProcessorConfig(BaseSettings):
    """Configuration for processors and exporters."""

    # VAST Database connection
    vast_host: str = "localhost"
    vast_port: int = 5432
    vast_database: str = "observability"
    vast_username: str = "vast_user"
    vast_password: str = "vast_password"
    vast_schema: str = "public"

    # Processing options
    enable_enrichment: bool = True
    enable_aggregation: bool = False
    aggregation_window: str = "5m"
    max_batch_size: int = 1000
    max_batch_age_seconds: int = 30

    # Data quality
    validate_data: bool = True
    drop_invalid: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
EOF

# vastdb_observability/models.py
cat > vastdb_observability/models.py << 'EOF'
from datetime import datetime
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
import uuid
import hashlib


class ProcessedMetric(BaseModel):
    """Normalized metric data for VAST Database."""

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

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProcessedLog(BaseModel):
    """Normalized log data for VAST Database."""

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

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ProcessedQuery(BaseModel):
    """Normalized query data for VAST Database."""

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

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

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
EOF

# vastdb_observability/processors/__init__.py
cat > vastdb_observability/processors/__init__.py << 'EOF'
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
EOF

# vastdb_observability/processors/base.py
cat > vastdb_observability/processors/base.py << 'EOF'
from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar, Generic, Optional
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class BaseProcessor(ABC, Generic[T]):
    """Base class for all processors."""

    def __init__(self, config: Optional["ProcessorConfig"] = None):
        from vastdb_observability.config import ProcessorConfig
        self.config = config or ProcessorConfig()
        self.logger = logger.bind(processor=self.__class__.__name__)

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> T:
        """Normalize raw data into common schema."""
        pass

    @abstractmethod
    def enrich(self, data: T) -> T:
        """Enrich data with computed fields and metadata."""
        pass

    def validate(self, data: T) -> bool:
        """Validate data quality."""
        if not self.config.validate_data:
            return True

        try:
            return True
        except Exception as e:
            self.logger.warning("validation_failed", error=str(e))
            return False

    def process(self, raw_data: Dict[str, Any], **kwargs) -> T:
        """Full processing pipeline: normalize -> enrich -> validate."""
        normalized = self.normalize(raw_data)

        if self.config.enable_enrichment and kwargs.get("enrich", True):
            normalized = self.enrich(normalized)

        if not self.validate(normalized):
            if self.config.drop_invalid:
                raise ValueError("Data validation failed")
            self.logger.warning("invalid_data_kept")

        return normalized
EOF

# vastdb_observability/processors/metrics.py
cat > vastdb_observability/processors/metrics.py << 'EOF'
from typing import Dict, Any, List
from datetime import datetime
from vastdb_observability.models import ProcessedMetric
from vastdb_observability.processors.base import BaseProcessor


class MetricsProcessor(BaseProcessor[List[ProcessedMetric]]):
    """Process OTLP metrics into normalized format."""

    def normalize(self, otlp_data: Dict[str, Any]) -> List[ProcessedMetric]:
        """Normalize OTLP metrics format to ProcessedMetric model."""
        metrics = []
        resource_attrs = self._extract_resource_attributes(otlp_data.get("resource", {}))

        for scope_metric in otlp_data.get("scopeMetrics", []):
            for metric in scope_metric.get("metrics", []):
                processed = self._process_metric(metric, resource_attrs)
                if processed:
                    metrics.extend(processed)

        return metrics

    def _extract_resource_attributes(self, resource: Dict) -> Dict[str, str]:
        """Extract key-value pairs from OTLP resource attributes."""
        attrs = {}
        for attr in resource.get("attributes", []):
            key = attr.get("key", "")
            value = attr.get("value", {})

            if "stringValue" in value:
                attrs[key] = value["stringValue"]
            elif "intValue" in value:
                attrs[key] = str(value["intValue"])
            elif "doubleValue" in value:
                attrs[key] = str(value["doubleValue"])

        return attrs

    def _process_metric(self, metric: Dict, resource_attrs: Dict[str, str]) -> List[ProcessedMetric]:
        """Process a single OTLP metric into ProcessedMetric objects."""
        metrics = []
        metric_name = metric.get("name", "unknown")
        unit = metric.get("unit", "")

        if "gauge" in metric:
            metric_type = "gauge"
            data_points = metric["gauge"].get("dataPoints", [])
        elif "sum" in metric:
            metric_type = "counter"
            data_points = metric["sum"].get("dataPoints", [])
        elif "histogram" in metric:
            metric_type = "histogram"
            data_points = metric["histogram"].get("dataPoints", [])
        else:
            return metrics

        for point in data_points:
            timestamp = self._parse_otlp_timestamp(point.get("timeUnixNano", 0))

            value = None
            if "asInt" in point:
                value = float(point["asInt"])
            elif "asDouble" in point:
                value = point["asDouble"]

            if value is None:
                continue

            point_attrs = self._extract_attributes(point.get("attributes", []))

            processed = ProcessedMetric(
                timestamp=timestamp,
                source=resource_attrs.get("db.system", "unknown"),
                host=resource_attrs.get("host.name", "unknown"),
                database_name=resource_attrs.get("db.name", "unknown"),
                environment=resource_attrs.get("deployment.environment", "production"),
                metric_name=metric_name,
                metric_value=value,
                metric_type=metric_type,
                unit=unit or None,
                tags=point_attrs,
                metadata={"description": metric.get("description", "")},
            )

            metrics.append(processed)

        return metrics

    def _extract_attributes(self, attributes: List[Dict]) -> Dict[str, str]:
        """Extract attributes from data point."""
        attrs = {}
        for attr in attributes:
            key = attr.get("key", "")
            value = attr.get("value", {})
            if "stringValue" in value:
                attrs[key] = value["stringValue"]
        return attrs

    def _parse_otlp_timestamp(self, time_unix_nano: int) -> datetime:
        """Convert OTLP nanosecond timestamp to datetime."""
        if time_unix_nano == 0:
            return datetime.utcnow()
        return datetime.fromtimestamp(time_unix_nano / 1_000_000_000)

    def enrich(self, metrics: List[ProcessedMetric]) -> List[ProcessedMetric]:
        """Enrich metrics with computed fields."""
        for metric in metrics:
            if "time" in metric.metric_name.lower() or "latency" in metric.metric_name.lower():
                if metric.metric_value < 100:
                    metric.tags["performance"] = "fast"
                elif metric.metric_value < 1000:
                    metric.tags["performance"] = "normal"
                else:
                    metric.tags["performance"] = "slow"

            if "error" in metric.metric_name.lower() or "deadlock" in metric.metric_name.lower():
                if metric.metric_value > 0:
                    metric.tags["severity"] = "warning"

        return metrics

    def process(self, otlp_data: Dict[str, Any], **kwargs) -> List[ProcessedMetric]:
        """Process OTLP metrics through full pipeline."""
        normalized = self.normalize(otlp_data)
        if self.config.enable_enrichment and kwargs.get("enrich", True):
            normalized = self.enrich(normalized)
        return normalized
EOF

# vastdb_observability/processors/logs.py
cat > vastdb_observability/processors/logs.py << 'EOF'
from typing import Dict, Any
from datetime import datetime
from vastdb_observability.models import ProcessedLog
from vastdb_observability.processors.base import BaseProcessor


class LogsProcessor(BaseProcessor[ProcessedLog]):
    """Process raw logs into normalized format."""

    def normalize(self, raw_log: Dict[str, Any]) -> ProcessedLog:
        """Normalize raw log format to ProcessedLog model."""
        payload = raw_log.get("payload", {})

        return ProcessedLog(
            timestamp=self._parse_timestamp(raw_log.get("timestamp")),
            source=raw_log.get("source", "unknown"),
            host=raw_log.get("host", "unknown"),
            database_name=raw_log.get("database", "unknown"),
            environment=raw_log.get("environment", "production"),
            log_level=raw_log.get("tags", {}).get("log_level", "info"),
            event_type=payload.get("event_type", "unknown"),
            message=self._build_message(payload),
            tags=raw_log.get("tags", {}),
            metadata=payload,
        )

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Parse timestamp string to datetime."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        if isinstance(timestamp_str, str):
            try:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                return datetime.utcnow()
        return datetime.utcnow()

    def _build_message(self, payload: Dict[str, Any]) -> str:
        """Build a human-readable message from payload."""
        event_type = payload.get("event_type", "unknown")

        if event_type == "deadlocks":
            count = payload.get("count", 0)
            return f"Detected {count} deadlock(s)"
        elif event_type == "connection_stats":
            total = payload.get("total", 0)
            active = payload.get("active", 0)
            return f"{active}/{total} active connections"
        elif event_type == "query_error":
            error_code = payload.get("error_code", "")
            error_msg = payload.get("error_message", "")
            return f"Query error {error_code}: {error_msg}"
        else:
            return f"Event: {event_type}"

    def enrich(self, log: ProcessedLog) -> ProcessedLog:
        """Enrich log with additional metadata."""
        if log.log_level in ["error", "critical"]:
            log.tags["requires_alert"] = "true"

        if "deadlock" in log.event_type.lower():
            log.tags["category"] = "concurrency"
        elif "connection" in log.event_type.lower():
            log.tags["category"] = "connection"
        elif "error" in log.event_type.lower():
            log.tags["category"] = "error"

        severity_map = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}
        log.metadata["severity_score"] = severity_map.get(log.log_level, 1)

        return log
EOF

# vastdb_observability/processors/queries.py
cat > vastdb_observability/processors/queries.py << 'EOF'
from typing import Dict, Any, Optional
from datetime import datetime
from vastdb_observability.models import ProcessedQuery
from vastdb_observability.processors.base import BaseProcessor


class QueriesProcessor(BaseProcessor[ProcessedQuery]):
    """Process raw query analytics into normalized format."""

    def normalize(self, raw_query: Dict[str, Any]) -> ProcessedQuery:
        """Normalize raw query format to ProcessedQuery model."""
        payload = raw_query.get("payload", {})
        query_text = payload.get("query", "")

        return ProcessedQuery(
            timestamp=self._parse_timestamp(raw_query.get("timestamp")),
            source=raw_query.get("source", "unknown"),
            host=raw_query.get("host", "unknown"),
            database_name=raw_query.get("database", "unknown"),
            environment=raw_query.get("environment", "production"),
            query_id=str(payload.get("queryid", "")),
            query_text=query_text[:500] if query_text else None,
            query_hash=ProcessedQuery.compute_query_hash(query_text) if query_text else None,
            calls=int(payload.get("calls", 0)),
            total_time_ms=float(payload.get("total_time_ms", 0.0)),
            mean_time_ms=float(payload.get("mean_time_ms", 0.0)),
            min_time_ms=self._safe_float(payload.get("min_time_ms")),
            max_time_ms=self._safe_float(payload.get("max_time_ms")),
            stddev_time_ms=self._safe_float(payload.get("stddev_time_ms")),
            rows_affected=self._safe_int(payload.get("rows")),
            cache_hit_ratio=self._safe_float(payload.get("cache_hit_ratio")),
            tags=raw_query.get("tags", {}),
            metadata=payload,
        )

    def _parse_timestamp(self, timestamp_str: Any) -> datetime:
        """Parse timestamp string to datetime."""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        if isinstance(timestamp_str, str):
            try:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                return datetime.utcnow()
        return datetime.utcnow()

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float."""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int."""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def enrich(self, query: ProcessedQuery) -> ProcessedQuery:
        """Enrich query with computed fields and classifications."""
        if query.mean_time_ms < 10:
            query.tags["performance"] = "excellent"
        elif query.mean_time_ms < 100:
            query.tags["performance"] = "good"
        elif query.mean_time_ms < 1000:
            query.tags["performance"] = "acceptable"
        else:
            query.tags["performance"] = "slow"

        if query.cache_hit_ratio is not None:
            if query.cache_hit_ratio > 0.95:
                query.tags["cache_efficiency"] = "excellent"
            elif query.cache_hit_ratio > 0.80:
                query.tags["cache_efficiency"] = "good"
            else:
                query.tags["cache_efficiency"] = "poor"

        if query.query_text:
            query_lower = query.query_text.lower()
            if "select" in query_lower:
                query.tags["query_type"] = "read"
            elif any(kw in query_lower for kw in ["insert", "update", "delete"]):
                query.tags["query_type"] = "write"

        if query.mean_time_ms > 1000:
            query.tags["requires_optimization"] = "true"

        if query.calls > 10000:
            query.tags["high_volume"] = "true"

        if query.mean_time_ms and query.stddev_time_ms:
            query.metadata["estimated_p95"] = query.mean_time_ms + (1.645 * query.stddev_time_ms)
            query.metadata["estimated_p99"] = query.mean_time_ms + (2.326 * query.stddev_time_ms)

        return query
EOF

# vastdb_observability/processors/batch.py
cat > vastdb_observability/processors/batch.py << 'EOF'
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
EOF

# vastdb_observability/processors/aggregator.py
cat > vastdb_observability/processors/aggregator.py << 'EOF'
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from vastdb_observability.models import ProcessedQuery


class Aggregator:
    """Aggregate time-series data into windows."""

    def __init__(self, window_size: str = "5m"):
        """Initialize aggregator with window size (1m, 5m, 15m, 1h, 1d)."""
        self.window_size = self._parse_window_size(window_size)

    def _parse_window_size(self, window: str) -> timedelta:
        """Parse window size string to timedelta."""
        value = int(window[:-1])
        unit = window[-1]

        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return timedelta(minutes=5)

    def _get_window_start(self, timestamp: datetime) -> datetime:
        """Get the start of the time window for a timestamp."""
        epoch = datetime(1970, 1, 1)
        seconds_since_epoch = (timestamp - epoch).total_seconds()
        window_seconds = self.window_size.total_seconds()
        window_number = int(seconds_since_epoch // window_seconds)
        return epoch + timedelta(seconds=window_number * window_seconds)

    def aggregate_queries(self, queries: List[ProcessedQuery]) -> List[Dict[str, Any]]:
        """Aggregate queries into time windows."""
        windows = defaultdict(lambda: defaultdict(list))

        for query in queries:
            window_start = self._get_window_start(query.timestamp)
            key = (window_start, query.query_hash or "unknown", query.host, query.database_name)
            windows[key].append(query)

        aggregated = []
        for (window_start, query_hash, host, database_name), query_list in windows.items():
            total_calls = sum(q.calls for q in query_list)
            total_time = sum(q.total_time_ms for q in query_list)
            mean_times = [q.mean_time_ms for q in query_list]

            aggregated.append({
                "window_start": window_start,
                "window_size": str(self.window_size),
                "query_hash": query_hash,
                "host": host,
                "database_name": database_name,
                "total_calls": total_calls,
                "total_time_ms": total_time,
                "avg_mean_time_ms": sum(mean_times) / len(mean_times),
                "min_mean_time_ms": min(mean_times),
                "max_mean_time_ms": max(mean_times),
                "sample_query": query_list[0].query_text,
            })

        return aggregated
EOF

# vastdb_observability/exporters/__init__.py
cat > vastdb_observability/exporters/__init__.py << 'EOF'
"""Exporter modules for writing processed data to storage."""

from vastdb_observability.exporters.vast import VASTExporter

__all__ = ["VASTExporter"]
EOF

# vastdb_observability/exporters/vast.py
cat > vastdb_observability/exporters/vast.py << 'EOF'
import asyncpg
from typing import List, Optional
import structlog
from vastdb_observability.models import ProcessedMetric, ProcessedLog, ProcessedQuery, ProcessorBatch
import json

logger = structlog.get_logger()


class VASTExporter:
    """Export processed data to VAST Database."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        schema: str = "public",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.schema = schema
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.logger = logger.bind(exporter="vast")

    async def connect(self):
        """Establish connection pool to VAST Database."""
        self.connection_pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            min_size=2,
            max_size=10,
        )
        self.logger.info("vast_connected", host=self.host)

    async def disconnect(self):
        """Close connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()
            self.logger.info("vast_disconnected")

    async def export_metrics(self, metrics: List[ProcessedMetric]):
        """Export metrics to db_metrics table."""
        if not metrics:
            return

        async with self.connection_pool.acquire() as conn:
            await conn.executemany(
                f"""
                INSERT INTO {self.schema}.db_metrics (
                    id, timestamp, source, host, database_name, environment,
                    metric_name, metric_value, metric_type, unit, tags, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                [
                    (
                        m.id, m.timestamp, m.source, m.host, m.database_name,
                        m.environment, m.metric_name, m.metric_value, m.metric_type,
                        m.unit, json.dumps(m.tags), json.dumps(m.metadata), m.created_at,
                    )
                    for m in metrics
                ],
            )

        self.logger.info("metrics_exported", count=len(metrics))

    async def export_logs(self, logs: List[ProcessedLog]):
        """Export logs to db_logs table."""
        if not logs:
            return

        async with self.connection_pool.acquire() as conn:
            await conn.executemany(
                f"""
                INSERT INTO {self.schema}.db_logs (
                    id, timestamp, source, host, database_name, environment,
                    log_level, event_type, message, tags, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                [
                    (
                        log.id, log.timestamp, log.source, log.host, log.database_name,
                        log.environment, log.log_level, log.event_type, log.message,
                        json.dumps(log.tags), json.dumps(log.metadata), log.created_at,
                    )
                    for log in logs
                ],
            )

        self.logger.info("logs_exported", count=len(logs))

    async def export_queries(self, queries: List[ProcessedQuery]):
        """Export queries to db_queries table."""
        if not queries:
            return

        async with self.connection_pool.acquire() as conn:
            await conn.executemany(
                f"""
                INSERT INTO {self.schema}.db_queries (
                    id, timestamp, source, host, database_name, environment,
                    query_id, query_text, query_hash, calls, total_time_ms, mean_time_ms,
                    min_time_ms, max_time_ms, stddev_time_ms, rows_affected, cache_hit_ratio,
                    tags, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                """,
                [
                    (
                        q.id, q.timestamp, q.source, q.host, q.database_name,
                        q.environment, q.query_id, q.query_text, q.query_hash,
                        q.calls, q.total_time_ms, q.mean_time_ms, q.min_time_ms,
                        q.max_time_ms, q.stddev_time_ms, q.rows_affected,
                        q.cache_hit_ratio, json.dumps(q.tags), json.dumps(q.metadata),
                        q.created_at,
                    )
                    for q in queries
                ],
            )

        self.logger.info("queries_exported", count=len(queries))

    async def export_batch(self, batch: ProcessorBatch):
        """Export a mixed batch of data."""
        if batch.is_empty():
            return

        if batch.metrics:
            await self.export_metrics(batch.metrics)
        if batch.logs:
            await self.export_logs(batch.logs)
        if batch.queries:
            await self.export_queries(batch.queries)

        self.logger.info("batch_exported", total=batch.size())
EOF

# ============================================================================
# Create Configuration Files
# ============================================================================
echo -e "${GREEN}Creating configuration files...${NC}"

# pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "vastdb-observability"
version = "1.0.0"
description = "Python library for processing database observability telemetry"
authors = [{name = "Your Organization"}]
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncpg>=0.29.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
EOF

# requirements.txt
cat > requirements.txt << 'EOF'
pydantic>=2.5.0
pydantic-settings>=2.1.0
asyncpg>=0.29.0
python-dotenv>=1.0.0
structlog>=24.1.0
EOF

# requirements-dev.txt
cat > requirements-dev.txt << 'EOF'
-r requirements.txt

pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0
EOF

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
EOF

# .env.example
cat > .env.example << 'EOF'
# VAST Database Configuration
VAST_HOST=localhost
VAST_PORT=5432
VAST_DATABASE=observability
VAST_USERNAME=vast_user
VAST_PASSWORD=secure_password
VAST_SCHEMA=public

# Processing Options
ENABLE_ENRICHMENT=true
ENABLE_AGGREGATION=false
AGGREGATION_WINDOW=5m
MAX_BATCH_SIZE=1000
MAX_BATCH_AGE_SECONDS=30

# Data Quality
VALIDATE_DATA=true
DROP_INVALID=false
EOF

echo -e "${GREEN}✓ Configuration files created${NC}"

# ============================================================================
# Create Test Files
# ============================================================================
echo -e "${GREEN}Creating test files...${NC}"

# tests/__init__.py
touch tests/__init__.py

# tests/conftest.py
cat > tests/conftest.py << 'EOF'
import pytest
from vastdb_observability.config import ProcessorConfig


@pytest.fixture
def config():
    """Test configuration."""
    return ProcessorConfig(
        vast_host="localhost",
        vast_port=5432,
        vast_database="test_db",
        vast_username="test_user",
        vast_password="test_pass",
    )
EOF

# tests/test_processors.py
cat > tests/test_processors.py << 'EOF'
import pytest
from vastdb_observability.processors.queries import QueriesProcessor
from vastdb_observability.processors.logs import LogsProcessor


def test_queries_processor_normalize():
    """Test query normalization."""
    processor = QueriesProcessor()

    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "123",
            "query": "SELECT * FROM users",
            "calls": 100,
            "total_time_ms": 1000.0,
            "mean_time_ms": 10.0,
        },
    }

    result = processor.normalize(raw_query)

    assert result.source == "postgresql"
    assert result.host == "test-host"
    assert result.database_name == "test_db"
    assert result.calls == 100
    assert result.mean_time_ms == 10.0


def test_queries_processor_enrich():
    """Test query enrichment."""
    processor = QueriesProcessor()

    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "123",
            "query": "SELECT * FROM users",
            "calls": 15000,
            "total_time_ms": 150000.0,
            "mean_time_ms": 10.0,
            "cache_hit_ratio": 0.95,
        },
    }

    result = processor.process(raw_query, enrich=True)

    assert result.tags["performance"] == "good"
    assert result.tags["cache_efficiency"] == "excellent"
    assert result.tags["high_volume"] == "true"
    assert result.tags["query_type"] == "read"


def test_logs_processor():
    """Test log processing."""
    processor = LogsProcessor()

    raw_log = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "log",
        "host": "test-host",
        "database": "test_db",
        "environment": "production",
        "tags": {"log_level": "warning"},
        "payload": {"event_type": "deadlocks", "count": 5},
    }

    result = processor.process(raw_log)

    assert result.log_level == "warning"
    assert result.event_type == "deadlocks"
    assert "5 deadlock" in result.message
EOF

echo -e "${GREEN}✓ Test files created${NC}"

# ============================================================================
# Create Example Files
# ============================================================================
echo -e "${GREEN}Creating example files...${NC}"

# examples/simple_usage.py
cat > examples/simple_usage.py << 'EOF'
"""Simple usage example for vastdb-observability library."""
import asyncio
from vastdb_observability import QueriesProcessor, VASTExporter


async def main():
    # Initialize processor
    processor = QueriesProcessor()

    # Initialize exporter
    exporter = VASTExporter(
        host="localhost",
        port=5432,
        database="observability",
        username="vast_user",
        password="vast_password",
    )
    await exporter.connect()

    # Simulate raw query data
    raw_query = {
        "timestamp": "2025-10-14T10:30:00.123456Z",
        "source": "postgresql",
        "data_type": "query",
        "host": "postgres-prod-1",
        "database": "app_db",
        "environment": "production",
        "tags": {},
        "payload": {
            "queryid": "1234567890",
            "query": "SELECT * FROM users WHERE id = $1",
            "calls": 1523,
            "total_time_ms": 45123.45,
            "mean_time_ms": 29.63,
        },
    }

    # Process
    processed = processor.process(raw_query, enrich=True)

    print(f"Processed query: {processed.query_text}")
    print(f"Performance: {processed.tags.get('performance')}")
    print(f"Query hash: {processed.query_hash}")

    # Export
    await exporter.export_queries([processed])
    print("✓ Exported to VAST Database")

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
EOF

# examples/batch_usage.py
cat > examples/batch_usage.py << 'EOF'
"""Batch processing example."""
import asyncio
from vastdb_observability import BatchProcessor, VASTExporter
from vastdb_observability.config import ProcessorConfig


async def main():
    # Configure
    config = ProcessorConfig(
        max_batch_size=100,
        max_batch_age_seconds=30,
        enable_enrichment=True,
    )

    # Initialize
    batch_processor = BatchProcessor(config)
    exporter = VASTExporter(
        host="localhost",
        port=5432,
        database="observability",
        username="vast_user",
        password="vast_password",
    )
    await exporter.connect()

    # Simulate processing multiple messages
    messages = [
        {
            "timestamp": "2025-10-14T10:30:00Z",
            "source": "postgresql",
            "data_type": "query",
            "host": "postgres-prod-1",
            "database": "app_db",
            "environment": "production",
            "tags": {},
            "payload": {
                "queryid": f"{i}",
                "query": "SELECT * FROM users",
                "calls": 100,
                "total_time_ms": 1000.0,
                "mean_time_ms": 10.0,
            },
        }
        for i in range(150)
    ]

    for message in messages:
        batch_processor.add(message)

        if batch_processor.should_flush():
            batch = batch_processor.get_batch()
            await exporter.export_batch(batch)
            print(f"Exported batch of {batch.size()} items")

    # Export any remaining
    batch = batch_processor.get_batch()
    if not batch.is_empty():
        await exporter.export_batch(batch)

    await exporter.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
EOF

echo -e "${GREEN}✓ Example files created${NC}"

# ============================================================================
# Create Documentation (Simplified versions)
# ============================================================================
echo -e "${GREEN}Creating documentation...${NC}"

# README.md
cat > README.md << 'EOF'
# vastdb-observability

Python library for processing database observability telemetry and storing it in VAST Database.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your VAST Database credentials

# Run example
python examples/simple_usage.py
```

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from vastdb_observability import QueriesProcessor, VASTExporter

processor = QueriesProcessor()
exporter = VASTExporter(
    host="vast.example.com",
    port=5432,
    database="observability",
    username="vast_user",
    password="secure_password"
)

await exporter.connect()

raw_query = {...}  # From Kafka
processed = processor.process(raw_query)
await exporter.export_queries([processed])
```

## Documentation

See `docs/` directory for detailed documentation:

- `ARCHITECTURE.md` - System architecture
- `API.md` - API reference
- `SETUP.md` - Setup guide

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=vastdb_observability
```

## License

Apache License 2.0
EOF

# Create simplified docs
cat > docs/ARCHITECTURE.md << 'EOF'
# Architecture

This library processes raw telemetry data and stores it in VAST Database.

## Components

- **Processors**: Normalize and enrich data
- **Exporters**: Write to VAST Database
- **Models**: Data structures

## Data Flow

```
Raw Data → Processor → Exporter → VAST Database
```

See full documentation in project artifacts.
EOF

cat > docs/API.md << 'EOF'
# API Reference

## Processors

### QueriesProcessor

```python
processor = QueriesProcessor()
processed = processor.process(raw_query)
```

### LogsProcessor

```python
processor = LogsProcessor()
processed = processor.process(raw_log)
```

## Exporters

### VASTExporter

```python
exporter = VASTExporter(host="...", port=5432, ...)
await exporter.connect()
await exporter.export_queries([...])
```

See full API documentation in project artifacts.
EOF

cat > docs/SETUP.md << 'EOF'
# Setup Guide

## Prerequisites

- Python 3.11+
- PostgreSQL/VAST Database
- pip

## Installation

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file
4. Run database schema (see `schema.sql`)

## Configuration

Edit `.env`:

```bash
VAST_HOST=localhost
VAST_PORT=5432
VAST_DATABASE=observability
VAST_USERNAME=vast_user
VAST_PASSWORD=secure_password
```

See full setup guide in project artifacts.
EOF

# Create LICENSE
cat > LICENSE << 'EOF'
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2025 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
EOF

echo -e "${GREEN}✓ Documentation created${NC}"

# ============================================================================
# Create Database Schema (simplified)
# ============================================================================
echo -e "${GREEN}Creating database schema...${NC}"

cat > schema.sql << 'EOF'
-- VAST Database Schema for Observability Data

CREATE SCHEMA IF NOT EXISTS observability;
SET search_path TO observability;

-- Metrics table
CREATE TABLE IF NOT EXISTS db_metrics (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_type VARCHAR(50),
    unit VARCHAR(50),
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON db_metrics(timestamp DESC);
CREATE INDEX idx_metrics_source_host ON db_metrics(source, host, database_name);
CREATE INDEX idx_metrics_name ON db_metrics(metric_name);

-- Logs table
CREATE TABLE IF NOT EXISTS db_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    log_level VARCHAR(20),
    event_type VARCHAR(100),
    message TEXT,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_timestamp ON db_logs(timestamp DESC);
CREATE INDEX idx_logs_source_host ON db_logs(source, host, database_name);
CREATE INDEX idx_logs_level ON db_logs(log_level);

-- Queries table
CREATE TABLE IF NOT EXISTS db_queries (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    query_id VARCHAR(255) NOT NULL,
    query_text TEXT,
    query_hash VARCHAR(64),
    calls BIGINT,
    total_time_ms DOUBLE PRECISION,
    mean_time_ms DOUBLE PRECISION,
    min_time_ms DOUBLE PRECISION,
    max_time_ms DOUBLE PRECISION,
    stddev_time_ms DOUBLE PRECISION,
    rows_affected BIGINT,
    cache_hit_ratio DOUBLE PRECISION,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_timestamp ON db_queries(timestamp DESC);
CREATE INDEX idx_queries_source_host ON db_queries(source, host, database_name);
CREATE INDEX idx_queries_hash ON db_queries(query_hash);
CREATE INDEX idx_queries_mean_time ON db_queries(mean_time_ms DESC);
EOF

echo -e "${GREEN}✓ Database schema created${NC}"

# ============================================================================
# Final Setup
# ============================================================================
echo -e "${GREEN}Finalizing setup...${NC}"

# Create a simple Makefile
cat > Makefile << 'EOF'
.PHONY: install test lint format clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check vastdb_observability/

format:
	black vastdb_observability/ tests/ examples/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/
EOF

# Create pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
EOF

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Project setup complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Project created in:${NC} $(pwd)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "  1. Install dependencies:"
echo "     ${BLUE}pip install -r requirements.txt${NC}"
echo ""
echo "  2. Configure environment:"
echo "     ${BLUE}cp .env.example .env${NC}"
echo "     ${BLUE}# Edit .env with your VAST Database credentials${NC}"
echo ""
echo "  3. Set up database:"
echo "     ${BLUE}psql -h localhost -U vast_user -d observability -f schema.sql${NC}"
echo ""
echo "  4. Run tests:"
echo "     ${BLUE}pytest${NC}"
echo ""
echo "  5. Try examples:"
echo "     ${BLUE}python examples/simple_usage.py${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - README.md         - Quick start"
echo "  - docs/SETUP.md     - Setup guide"
echo "  - docs/API.md       - API reference"
echo "  - examples/         - Usage examples"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
