"""
VAST Exporter - Updated for the new extensible, entity-centric schema.
This module handles writing processed data to the 'events', 'metrics', and
'entities' tables in VAST Database using the official VAST API.
"""
import pyarrow as pa
from typing import List
import structlog
from vastdb_observability.models import Event, Metric, Entity, ProcessorBatch
import json
from datetime import datetime

logger = structlog.get_logger()


class VASTExporter:
    """Exports processed data to VAST Database using the extensible schema."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, schema_name: str = "observability"):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.schema_name = schema_name
        self.session = None
        self.logger = logger.bind(exporter="vast")

        if not endpoint.startswith(('http://', 'https://')):
            raise ValueError(f"Endpoint must start with http:// or https://, got: {endpoint}")

    async def connect(self):
        """Establishes a session with the VAST Database."""
        import vastdb
        self.session = vastdb.connect(endpoint=self.endpoint, access=self.access_key, secret=self.secret_key)
        self.logger.info("vast_connected", endpoint=self.endpoint, bucket=self.bucket_name)

    async def disconnect(self):
        """Closes the session."""
        self.session = None
        self.logger.info("vast_disconnected")

    def _to_us(self, dt: datetime) -> int:
        """Converts a datetime object to microseconds since epoch."""
        return int(dt.timestamp() * 1_000_000)

    async def export_events(self, events: List[Event]):
        """Exports a batch of events to the 'events' table."""
        if not events:
            return

        arrays = {
            'timestamp': pa.array([self._to_us(e.timestamp) for e in events], type=pa.timestamp('us')),
            'entity_id': pa.array([e.entity_id for e in events]),
            'event_type': pa.array([e.event_type for e in events]),
            'source': pa.array([e.source for e in events]),
            'environment': pa.array([e.environment for e in events]),
            'message': pa.array([e.message for e in events]),
            'tags': pa.array([json.dumps(e.tags) for e in events]),
            'attributes': pa.array([json.dumps(e.attributes) for e in events]),
            'trace_id': pa.array([e.trace_id for e in events], type=pa.string()),
            'id': pa.array([e.id for e in events]),
            'created_at': pa.array([self._to_us(e.created_at) for e in events], type=pa.timestamp('us')),
        }
        batch = pa.RecordBatch.from_pydict(arrays)

        with self.session.transaction() as tx:
            table = tx.bucket(self.bucket_name).schema(self.schema_name).table('events')
            table.insert(batch)
        self.logger.info("events_exported", count=len(events))

    async def export_metrics(self, metrics: List[Metric]):
        """Exports a batch of metrics to the 'metrics' table."""
        if not metrics:
            return

        arrays = {
            'metric_name': pa.array([m.metric_name for m in metrics]),
            'entity_id': pa.array([m.entity_id for m in metrics]),
            'timestamp': pa.array([self._to_us(m.timestamp) for m in metrics], type=pa.timestamp('us')),
            'source': pa.array([m.source for m in metrics]),
            'environment': pa.array([m.environment for m in metrics]),
            'metric_value': pa.array([m.metric_value for m in metrics]),
            'metric_type': pa.array([m.metric_type for m in metrics]),
            'unit': pa.array([m.unit for m in metrics], type=pa.string()),
            'tags': pa.array([json.dumps(m.tags) for m in metrics]),
            'metadata': pa.array([json.dumps(m.metadata) for m in metrics]),
            'id': pa.array([m.id for m in metrics]),
            'created_at': pa.array([self._to_us(m.created_at) for m in metrics], type=pa.timestamp('us')),
        }
        batch = pa.RecordBatch.from_pydict(arrays)

        with self.session.transaction() as tx:
            table = tx.bucket(self.bucket_name).schema(self.schema_name).table('metrics')
            table.insert(batch)
        self.logger.info("metrics_exported", count=len(metrics))

    async def export_entities(self, entities: List[Entity]):
        """Exports a batch of entities to the 'entities' table."""
        if not entities:
            return

        arrays = {
            'entity_id': pa.array([e.entity_id for e in entities]),
            'entity_type': pa.array([e.entity_type for e in entities]),
            'first_seen': pa.array([self._to_us(e.first_seen) for e in entities], type=pa.timestamp('us')),
            'last_seen': pa.array([self._to_us(e.last_seen) for e in entities], type=pa.timestamp('us')),
            'attributes': pa.array([json.dumps(e.attributes) for e in entities]),
        }
        batch = pa.RecordBatch.from_pydict(arrays)

        with self.session.transaction() as tx:
            table = tx.bucket(self.bucket_name).schema(self.schema_name).table('entities')
            table.insert(batch)
        self.logger.info("entities_exported", count=len(entities))


    async def export_batch(self, batch: ProcessorBatch):
        """Exports a mixed batch of events and metrics."""
        if batch.is_empty():
            return

        # --- FIX IS HERE ---
        # Only export events and metrics, since the batch object
        # does not contain an 'entities' attribute.
        if batch.events:
            await self.export_events(batch.events)
        if batch.metrics:
            await self.export_metrics(batch.metrics)
            
        self.logger.info("batch_exported", total=batch.size(), events=len(batch.events), metrics=len(batch.metrics))