"""
Updated VAST Exporter aligned with Arrow schema and sorting keys.

Replace library/vastdb_observability/exporters/vast.py with this implementation.
"""

import pyarrow as pa
from typing import List, Optional
import structlog
from vastdb_observability.models import ProcessedMetric, ProcessedLog, ProcessedQuery, ProcessorBatch
import json
from datetime import datetime

logger = structlog.get_logger()


class VASTExporter:
    """Export processed data to VAST Database using PyArrow."""

    def __init__(
        self,
        endpoint: str,  # e.g., "http://vast.example.com:5432"
        access_key: str,
        secret_key: str,
        database: str,
        schema: str = "observability",
    ):
        """
        Initialize VAST exporter.
        
        Args:
            endpoint: VAST endpoint URL (http://host:port)
            access_key: VAST access key
            secret_key: VAST secret key
            database: Database name
            schema: Schema name (default: observability)
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.database_name = database
        self.schema_name = schema
        self.session = None
        self.db_schema = None
        self.logger = logger.bind(exporter="vast")

    async def connect(self):
        """Establish connection to VAST Database."""
        from vastdb import connect
        
        self.session = connect(
            endpoint=self.endpoint,
            access=self.access_key,
            secret=self.secret_key
        )
        
        database = self.session.database(self.database_name)
        self.db_schema = database.schema(self.schema_name)
        
        self.logger.info(
            "vast_connected",
            endpoint=self.endpoint,
            database=self.database_name,
            schema=self.schema_name
        )

    async def disconnect(self):
        """Close connection."""
        if self.session:
            # vastdb sessions don't need explicit closing
            self.session = None
            self.logger.info("vast_disconnected")

    def _convert_timestamp(self, dt: datetime) -> int:
        """Convert datetime to microseconds since epoch."""
        return int(dt.timestamp() * 1_000_000)

    async def export_metrics(self, metrics: List[ProcessedMetric]):
        """Export metrics to db_metrics table."""
        if not metrics:
            return

        # Convert to PyArrow RecordBatch with column order matching schema
        # Sorting keys first: timestamp, host, database_name, metric_name
        arrays = {
            'timestamp': pa.array([self._convert_timestamp(m.timestamp) for m in metrics], 
                                 type=pa.timestamp('us')),
            'host': pa.array([m.host for m in metrics]),
            'database_name': pa.array([m.database_name for m in metrics]),
            'metric_name': pa.array([m.metric_name for m in metrics]),
            'source': pa.array([m.source for m in metrics]),
            'environment': pa.array([m.environment for m in metrics]),
            'metric_value': pa.array([m.metric_value for m in metrics]),
            'metric_type': pa.array([m.metric_type for m in metrics]),
            'unit': pa.array([m.unit for m in metrics]),
            'tags': pa.array([json.dumps(m.tags) for m in metrics]),
            'metadata': pa.array([json.dumps(m.metadata) for m in metrics]),
            'created_at': pa.array([self._convert_timestamp(m.created_at) for m in metrics],
                                  type=pa.timestamp('us')),
            'id': pa.array([m.id for m in metrics]),
        }

        # Create RecordBatch in the correct column order
        batch = pa.RecordBatch.from_pydict(arrays)
        
        # Insert into VAST
        table = self.db_schema.table('db_metrics')
        table.insert(batch)

        self.logger.info("metrics_exported", count=len(metrics))

    async def export_logs(self, logs: List[ProcessedLog]):
        """Export logs to db_logs table."""
        if not logs:
            return

        # Column order: timestamp, host, database_name, log_level (sorting keys first)
        arrays = {
            'timestamp': pa.array([self._convert_timestamp(log.timestamp) for log in logs],
                                 type=pa.timestamp('us')),
            'host': pa.array([log.host for log in logs]),
            'database_name': pa.array([log.database_name for log in logs]),
            'log_level': pa.array([log.log_level for log in logs]),
            'source': pa.array([log.source for log in logs]),
            'environment': pa.array([log.environment for log in logs]),
            'event_type': pa.array([log.event_type for log in logs]),
            'message': pa.array([log.message for log in logs]),
            'tags': pa.array([json.dumps(log.tags) for log in logs]),
            'metadata': pa.array([json.dumps(log.metadata) for log in logs]),
            'created_at': pa.array([self._convert_timestamp(log.created_at) for log in logs],
                                  type=pa.timestamp('us')),
            'id': pa.array([log.id for log in logs]),
        }

        batch = pa.RecordBatch.from_pydict(arrays)
        
        table = self.db_schema.table('db_logs')
        table.insert(batch)

        self.logger.info("logs_exported", count=len(logs))

    async def export_queries(self, queries: List[ProcessedQuery]):
        """Export queries to db_queries table."""
        if not queries:
            return

        # Column order: timestamp, host, database_name, mean_time_ms (sorting keys first)
        arrays = {
            'timestamp': pa.array([self._convert_timestamp(q.timestamp) for q in queries],
                                 type=pa.timestamp('us')),
            'host': pa.array([q.host for q in queries]),
            'database_name': pa.array([q.database_name for q in queries]),
            'mean_time_ms': pa.array([q.mean_time_ms for q in queries]),
            'source': pa.array([q.source for q in queries]),
            'environment': pa.array([q.environment for q in queries]),
            'query_id': pa.array([q.query_id for q in queries]),
            'query_text': pa.array([q.query_text for q in queries]),
            'query_hash': pa.array([q.query_hash for q in queries]),
            'calls': pa.array([q.calls for q in queries]),
            'total_time_ms': pa.array([q.total_time_ms for q in queries]),
            'min_time_ms': pa.array([q.min_time_ms for q in queries]),
            'max_time_ms': pa.array([q.max_time_ms for q in queries]),
            'stddev_time_ms': pa.array([q.stddev_time_ms for q in queries]),
            'rows_affected': pa.array([q.rows_affected for q in queries]),
            'cache_hit_ratio': pa.array([q.cache_hit_ratio for q in queries]),
            'tags': pa.array([json.dumps(q.tags) for q in queries]),
            'metadata': pa.array([json.dumps(q.metadata) for q in queries]),
            'created_at': pa.array([self._convert_timestamp(q.created_at) for q in queries],
                                  type=pa.timestamp('us')),
            'id': pa.array([q.id for q in queries]),
        }

        batch = pa.RecordBatch.from_pydict(arrays)
        
        table = self.db_schema.table('db_queries')
        table.insert(batch)

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


# Example usage:
"""
from vastdb_observability import QueriesProcessor, VASTExporter

processor = QueriesProcessor()
exporter = VASTExporter(
    endpoint="http://vast.example.com:5432",
    access_key="your-access-key",
    secret_key="your-secret-key",
    database="observability",
    schema="observability"
)

await exporter.connect()

raw_query = {...}
processed = processor.process(raw_query)
await exporter.export_queries([processed])

await exporter.disconnect()
"""