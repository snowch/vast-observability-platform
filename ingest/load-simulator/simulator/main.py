import asyncio
import random
import structlog
from simulator.config import Settings
from simulator.query_generator import QueryGenerator
from simulator.syslog_generator import SyslogGenerator

logger = structlog.get_logger()

class LoadSimulator:
    def __init__(self):
        self.settings = Settings()
        self.query_generator = None
        self.syslog_generator = None
        self.running = False
        self.stats = {'total': 0, 'successful_queries': 0, 'failed_queries': 0, 'syslogs_sent': 0}
    
    async def initialize(self):
        logger.info("initializing_load_simulator", query_rate=self.settings.QUERY_RATE)
        
        # Initialize Query Generator
        self.query_generator = QueryGenerator(
            self.settings.POSTGRES_HOST, self.settings.POSTGRES_PORT,
            self.settings.POSTGRES_DB, self.settings.POSTGRES_USER,
            self.settings.POSTGRES_PASSWORD
        )
        await self.query_generator.connect()
        
        # Initialize Syslog Generator
        self.syslog_generator = SyslogGenerator(
            self.settings.OTEL_COLLECTOR_HOST,
            self.settings.OTEL_COLLECTOR_SYSLOG_PORT
        )
        await self.syslog_generator.connect()

    async def generate_workload(self):
        self.stats['total'] += 1
        
        # Decide whether to send a syslog message or a query
        if random.random() < self.settings.SYSLOG_PROBABILITY:
            await self.syslog_generator.send_log()
            self.stats['syslogs_sent'] += 1
        else:
            try:
                is_slow = random.random() < self.settings.SLOW_QUERY_PROBABILITY
                is_write = random.random() < self.settings.WRITE_PROBABILITY
                
                if is_slow:
                    await self.query_generator.execute_slow_query()
                elif is_write:
                    await self.query_generator.insert_user()
                else:
                    if random.random() < 0.5:
                        await self.query_generator.simple_select()
                    else:
                        await self.query_generator.join_query()
                
                self.stats['successful_queries'] += 1
            except Exception as e:
                self.stats['failed_queries'] += 1
                logger.error("query_failed", error=str(e))
    
    async def run_continuous_load(self):
        delay = 1.0 / self.settings.QUERY_RATE if self.settings.QUERY_RATE > 0 else 1.0
        while self.running:
            try:
                await self.generate_workload()
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
    
    async def stats_reporter(self):
        while self.running:
            await asyncio.sleep(60)
            logger.info("load_simulator_stats", **self.stats)
    
    async def run(self):
        self.running = True
        await self.initialize()
        tasks = [
            asyncio.create_task(self.run_continuous_load()),
            asyncio.create_task(self.stats_reporter())
        ]
        await asyncio.gather(*tasks)
    
    async def shutdown(self):
        self.running = False
        if self.query_generator:
            await self.query_generator.disconnect()
        if self.syslog_generator:
            await self.syslog_generator.disconnect()

async def main():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    simulator = LoadSimulator()
    try:
        await simulator.run()
    finally:
        await simulator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())