#!/bin/bash
# ============================================================================
# VAST Observability Processor Project Setup Script
# ============================================================================
# This script creates the processor subproject, which consumes data from Kafka,
# processes it using the vastdb-observability library, and exports it to
# VAST Database.
#
# Usage: ./create_processor_project.sh
# ============================================================================

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project name
PROJECT_NAME="processor"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  VAST Observability Processor Setup${NC}"
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
# Create Dockerfile
# ============================================================================
echo -e "${GREEN}Creating Dockerfile...${NC}"
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for librdkafka
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the processor application code
COPY processor/ ./processor/

# Copy the library code to be installed
COPY library/ ./library/
RUN pip install ./library/

# Create a non-root user
RUN useradd -m -u 1000 processor && chown -R processor:processor /app
USER processor

CMD ["python", "-m", "processor.main"]
EOF

# ============================================================================
# Create requirements.txt
# ============================================================================
echo -e "${GREEN}Creating requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
# Kafka client
confluent-kafka==2.3.0

# Configuration and logging
pydantic-settings==2.1.0
python-dotenv==1.0.0
structlog==24.1.0

# The vastdb-observability library will be installed from the local copy
EOF

# ============================================================================
# Create Application Structure
# ============================================================================
echo -e "${GREEN}Creating application structure...${NC}"
mkdir -p processor

# processor/__init__.py
touch processor/__init__.py

# processor/config.py
cat > processor/config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-ingestion:9092"
    KAFKA_GROUP_ID: str = "vastdb_processor"
    KAFKA_TOPICS: str = "raw-logs,raw-queries"

    # VAST Database Configuration
    VAST_ENDPOINT: str = "http://localhost:5432"
    VAST_ACCESS_KEY: str = "your-access-key"
    VAST_SECRET_KEY: str = "your-secret-key"
    VAST_BUCKET: str = "observability"

    # Batching Configuration
    MAX_BATCH_SIZE: int = 100
    MAX_BATCH_AGE_SECONDS: int = 10

    class Config:
        env_file = ".env"
EOF

# processor/main.py
cat > processor/main.py << 'EOF'
import asyncio
import json
import signal
import sys
import time
from confluent_kafka import Consumer, KafkaError
import structlog
from vastdb_observability import BatchProcessor, VASTExporter
from .config import Settings

logger = structlog.get_logger()

class KafkaProcessorService:
    def __init__(self):
        self.settings = Settings()
        self.running = True
        self.consumer = None
        self.batch_processor = None
        self.exporter = None

    async def initialize(self):
        """Initializes all components of the service."""
        logger.info("initializing_processor_service")

        # Configure Kafka consumer
        consumer_conf = {
            'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': self.settings.KAFKA_GROUP_ID,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        self.consumer = Consumer(consumer_conf)
        self.consumer.subscribe(self.settings.KAFKA_TOPICS.split(','))
        logger.info("kafka_consumer_subscribed", topics=self.settings.KAFKA_TOPICS)

        # Initialize the batch processor from the library
        self.batch_processor = BatchProcessor(config=self.settings)

        # Initialize the VAST exporter
        self.exporter = VASTExporter(
            endpoint=self.settings.VAST_ENDPOINT,
            access_key=self.settings.VAST_ACCESS_KEY,
            secret_key=self.settings.VAST_SECRET_KEY,
            bucket_name=self.settings.VAST_BUCKET
        )
        await self.exporter.connect()
        logger.info("vast_exporter_connected")

    def consume_loop(self):
        """The main loop to consume messages from Kafka."""
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # No message received within timeout
                    if self.batch_processor.should_flush():
                        asyncio.run(self.flush_batch())
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error("kafka_consumer_error", error=msg.error())
                        break

                # Process the message
                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                    self.batch_processor.add(message_data)
                    self.consumer.commit(asynchronous=True)
                except json.JSONDecodeError:
                    logger.warning("invalid_json_message", topic=msg.topic(), partition=msg.partition(), offset=msg.offset())
                except Exception as e:
                    logger.error("message_processing_failed", error=str(e))

                # Check if batch should be flushed
                if self.batch_processor.should_flush():
                    asyncio.run(self.flush_batch())

        finally:
            self.consumer.close()

    async def flush_batch(self):
        """Flushes the current batch to VAST DB."""
        batch = self.batch_processor.get_batch()
        if not batch.is_empty():
            logger.info("flushing_batch", size=batch.size())
            await self.exporter.export_batch(batch)
            logger.info("batch_flushed_successfully")

    async def shutdown(self):
        """Shuts down the service gracefully."""
        self.running = False
        logger.info("shutting_down_processor")
        if self.exporter:
            # Flush any remaining items before shutting down
            await self.flush_batch()
            await self.exporter.disconnect()
        logger.info("processor_shutdown_complete")

def main():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )

    service = KafkaProcessorService()
    loop = asyncio.get_event_loop()

    def handle_signal(sig):
        logger.info(f"received_signal_{sig},_shutting_down")
        loop.create_task(service.shutdown())

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(service.initialize())
        service.consume_loop()
    except Exception as e:
        logger.error("service_startup_failed", error=str(e))
    finally:
        logger.info("service_terminated")

if __name__ == "__main__":
    main()
EOF

# ============================================================================
# Create Supporting Files
# ============================================================================
echo -e "${GREEN}Creating supporting files...${NC}"

# .env.example
cat > .env.example << 'EOF'
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9093
KAFKA_GROUP_ID=vastdb_processor_local
KAFKA_TOPICS=raw-logs,raw-queries

# VAST Database Connection
VAST_ENDPOINT=http://localhost:5432
VAST_ACCESS_KEY=your-access-key
VAST_SECRET_KEY=your-secret-key
VAST_BUCKET=observability

# Batching Configuration
MAX_BATCH_SIZE=100
MAX_BATCH_AGE_SECONDS=10
EOF

# README.md
cat > README.md << 'EOF'
# VAST Observability - Processor

This project is the processing layer of the VAST Observability Platform. It consumes raw telemetry data from Kafka, uses the `vastdb-observability` library to process it, and exports the enriched data to VAST Database.

## Overview

- **Input**: Consumes from `raw-logs` and `raw-queries` Kafka topics.
- **Processing**: Uses the `BatchProcessor` from the `vastdb-observability` library to normalize and enrich data in batches.
- **Output**: Writes processed data to `events` and `metrics` tables in VAST Database via the `VASTExporter`.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- The `ingest` project must be running to provide data.
- The `vastdb-observability` library must be present in the parent directory.

### Running the Processor

1.  **Configure Environment**:
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Edit `.env` with your VAST Database credentials and Kafka connection details.

2.  **Build and Run with Docker Compose**:
    -   A `docker-compose.yml` file should be created in the root of the `vast-observability-platform` directory to run this service alongside the `ingest` services.

    ```yaml
    # In root docker-compose.yml
    services:
      # ... (ingest services) ...

      processor:
        build:
          context: ./processor
          dockerfile: Dockerfile
        container_name: processor
        depends_on:
          - kafka-ingestion
        environment:
          - KAFKA_BOOTSTRAP_SERVERS=kafka-ingestion:9092
          - VAST_ENDPOINT=${VAST_ENDPOINT}
          - VAST_ACCESS_KEY=${VAST_ACCESS_KEY}
          - VAST_SECRET_KEY=${VAST_SECRET_KEY}
          - VAST_BUCKET=${VAST_BUCKET}
        volumes:
          - ./library:/app/library # Mount the local library for development
        restart: unless-stopped
    ```

3.  **Start the Service**:
    -   From the root directory:
        ```bash
        docker-compose up -d --build processor
        ```

4.  **View Logs**:
    ```bash
    docker-compose logs -f processor
    ```

## How It Works

1.  The `KafkaProcessorService` starts and initializes a Kafka consumer, a `BatchProcessor`, and a `VASTExporter`.
2.  It subscribes to the `raw-logs` and `raw-queries` topics.
3.  The `consume_loop` continuously polls Kafka for new messages.
4.  Each raw message is added to the `BatchProcessor`, which normalizes and enriches it into a structured `Event` or `Metric` object.
5.  The `BatchProcessor` accumulates items until its `max_batch_size` or `max_batch_age_seconds` is reached.
6.  When the batch is ready to be flushed, the `VASTExporter` is used to write the entire batch to the appropriate tables in VAST Database.
7.  Kafka offsets are committed after each message is successfully added to the batch, ensuring at-least-once processing semantics.
EOF

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Processor project setup complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}Project created in:${NC} $(pwd)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "  1. Add the processor service to the main 'docker-compose.yml' in the parent directory."
echo "  2. Copy '.env.example' to '.env' and fill in your VAST Database credentials."
echo "  3. Build and run the service: 'docker-compose up -d --build processor'"
echo ""
