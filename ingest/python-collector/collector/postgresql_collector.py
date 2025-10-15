import asyncpg
from datetime import datetime
from typing import List, Optional
import structlog
from collector.models import ObservabilityData

logger = structlog.get_logger()

class PostgreSQLCollector:
    def __init__(self, host, port, database, username, password, environment="production"):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.environment = environment
        self.connection_pool = None
    
    async def connect(self):
        self.connection_pool = await asyncpg.create_pool(
            host=self.host, port=self.port, user=self.username,
            password=self.password, database=self.database,
            min_size=1, max_size=5
        )
        logger.info("postgresql_connected", host=self.host)
    
    async def disconnect(self):
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def collect_logs(self) -> List[ObservabilityData]:
        data_points = []
        async with self.connection_pool.acquire() as conn:
            # Existing deadlock check
            errors = await conn.fetchrow("""
                SELECT deadlocks FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            if errors and errors['deadlocks'] > 0:
                data_points.append(ObservabilityData(
                    timestamp=datetime.utcnow(),
                    source="postgresql", data_type="log",
                    host=self.host, database=self.database,
                    environment=self.environment,
                    tags={"log_level": "warning"},
                    payload={"event_type": "deadlocks", "count": errors['deadlocks']}
                ))
            
            # NEW: Log connection stats every cycle
            connections = await conn.fetchrow("""
                SELECT 
                    count(*) as total,
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle
                FROM pg_stat_activity
            """)
            
            data_points.append(ObservabilityData(
                timestamp=datetime.utcnow(),
                source="postgresql", data_type="log",
                host=self.host, database=self.database,
                environment=self.environment,
                tags={"log_level": "info"},
                payload={
                    "event_type": "connection_stats",
                    "total": connections['total'],
                    "active": connections['active'],
                    "idle": connections['idle']
                }
            ))
        
        return data_points
    
    async def collect_query_analytics(self) -> List[ObservabilityData]:
        data_points = []
        async with self.connection_pool.acquire() as conn:
            has_pg_stat = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements')"
            )
            if has_pg_stat:
                queries = await conn.fetch("""
                    SELECT queryid, query, calls, total_exec_time, mean_exec_time
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat%'
                    ORDER BY total_exec_time DESC LIMIT 20
                """)
                for row in queries:
                    data_points.append(ObservabilityData(
                        timestamp=datetime.utcnow(),
                        source="postgresql", data_type="query",
                        host=self.host, database=self.database,
                        environment=self.environment, tags={},
                        payload={
                            "queryid": str(row['queryid']),
                            "query": row['query'][:500],
                            "calls": row['calls'],
                            "total_time_ms": float(row['total_exec_time']),
                            "mean_time_ms": float(row['mean_exec_time'])
                        }
                    ))
        return data_points
