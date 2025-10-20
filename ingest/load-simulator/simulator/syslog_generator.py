import asyncio
import random
from faker import Faker
from datetime import datetime
import structlog

logger = structlog.get_logger()
fake = Faker()

class SyslogGenerator:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.writer = None

    async def connect(self):
        """Establishes a connection to the syslog receiver."""
        try:
            _, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info("syslog_generator_connected", host=self.host, port=self.port)
        except Exception as e:
            logger.error("syslog_connection_failed", error=str(e))
            self.writer = None

    async def disconnect(self):
        """Closes the connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("syslog_generator_disconnected")

    async def send_log(self):
        """Sends a single, fake syslog message."""
        if not self.writer:
            logger.warning("syslog_writer_not_available_skipping_send")
            # Attempt to reconnect
            await self.connect()
            if not self.writer:
                return

        try:
            # RFC3164 format: <PRI>TIMESTAMP HOSTNAME TAG: MESSAGE
            pri = f"<{random.randint(1, 191)}>"
            timestamp = datetime.now().strftime("%b %d %H:%M:%S")
            hostname = fake.hostname()
            tag = random.choice(["sshd", "cron", "kernel", "sudo"])
            message = fake.sentence(nb_words=10)
            
            syslog_message = f"{pri}{timestamp} {hostname} {tag}: {message}\n"
            
            self.writer.write(syslog_message.encode('utf-8'))
            await self.writer.drain()
        except Exception as e:
            logger.error("syslog_send_failed", error=str(e))
            # Connection might be lost, reset writer to trigger reconnect
            self.writer = None