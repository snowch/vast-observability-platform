import json
from typing import List, Optional
from aiokafka import AIOKafkaProducer
import structlog
from collector.models import ObservabilityData

logger = structlog.get_logger()

class KafkaExporter:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
    
    async def connect(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        await self.producer.start()
        logger.info("kafka_connected")
    
    async def disconnect(self):
        if self.producer:
            await self.producer.stop()
    
    async def export(self, data: List[ObservabilityData], topic: str = "raw-data"):
        if not data:
            return
        for item in data:
            await self.producer.send(
                topic=topic,
                value=item.to_kafka_message(),
                key=f"{item.host}:{item.database}".encode('utf-8')
            )
        await self.producer.flush()
        logger.info("data_exported", topic=topic, count=len(data))
