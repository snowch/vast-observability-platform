import asyncio
import signal
import sys
import structlog
from collector.config import Settings
from collector.postgresql_collector import PostgreSQLCollector
from collector.kafka_exporter import KafkaExporter

logger = structlog.get_logger()

class CollectorService:
    def __init__(self):
        self.settings = Settings()
        self.collector = None
        self.exporter = None
        self.running = False
    
    async def initialize(self):
        logger.info("initializing_collector")
        self.collector = PostgreSQLCollector(
            host=self.settings.POSTGRES_HOST,
            port=self.settings.POSTGRES_PORT,
            database=self.settings.POSTGRES_DB,
            username=self.settings.POSTGRES_USER,
            password=self.settings.POSTGRES_PASSWORD,
            environment=self.settings.ENVIRONMENT
        )
        await self.collector.connect()
        
        self.exporter = KafkaExporter(self.settings.KAFKA_BOOTSTRAP_SERVERS)
        await self.exporter.connect()
        logger.info("collector_initialized")
    
    async def collect_and_export(self):
        try:
            logs = await self.collector.collect_logs()
            if logs:
                await self.exporter.export(logs, topic="raw-logs")
            
            queries = await self.collector.collect_query_analytics()
            if queries:
                await self.exporter.export(queries, topic="raw-queries")
        except Exception as e:
            logger.error("collection_failed", error=str(e))
    
    async def collection_loop(self):
        while self.running:
            try:
                await self.collect_and_export()
                await asyncio.sleep(self.settings.COLLECTION_INTERVAL)
            except asyncio.CancelledError:
                break
    
    async def run(self):
        self.running = True
        await self.initialize()
        await self.collection_loop()
    
    async def shutdown(self):
        self.running = False
        if self.collector:
            await self.collector.disconnect()
        if self.exporter:
            await self.exporter.disconnect()

async def main():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    service = CollectorService()
    try:
        await service.run()
    finally:
        await service.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
