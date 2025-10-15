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
