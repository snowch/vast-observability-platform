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

## Data Mapping to VAST Tables

The collectors in this project produce raw data to Kafka topics. A separate `processor` service consumes this data and maps it to the VAST Database tables as follows:

| Kafka Topic | Producer | Processor | VAST Table | Details |
| :--- | :--- | :--- | :--- | :--- |
| `raw-logs` | Python Collector | `LogsProcessor` | **`events`** | Each log message becomes a row with `event_type` = `'log'`. |
| `raw-queries` | Python Collector | `QueriesProcessor` | **`events`** | Each query analytics message becomes a row with `event_type` = `'database_query'`. |
| `otel-metrics` | OTel Collector | `MetricsProcessor` | **`metrics`** | Each metric data point becomes a row linked to a host via `entity_id`. |

**Note**: The **`entities`** table is not populated by this pipeline. It requires a separate discovery or inventory process to catalog the systems being monitored.
