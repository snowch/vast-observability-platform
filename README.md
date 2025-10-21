# VAST Observability Platform

Complete database observability platform for collecting, processing, and analyzing database telemetry.

## Project Structure

```
vast-observability-platform/
├── ingest/                  # Data collection layer (OTel & Python collectors)
│   ├── docker-compose.yml   # Services: PostgreSQL, Kafka, Collectors, etc.
│   ├── Makefile             # Commands for managing the ingest layer
│   └── ...
├── library/                 # Core Python library for data processing
│   ├── vastdb_observability/ # Normalizes, enriches, and models telemetry data
│   └── ...
├── processor/               # Kafka consumer to process and store data in VAST DB
│   ├── Dockerfile           # Runs the processor service using the library
│   └── ...
└── query/                   # Scripts for querying data from VAST DB
    └── ...
```

## Data Collection Strategies

This project intentionally demonstrates two different approaches to data collection to showcase flexibility:

1.  **Standard OpenTelemetry (OTLP)**: The OpenTelemetry Collector is used to gather standard metrics and logs. This is the recommended approach for interoperability with the wider observability ecosystem.

      * **Metrics (`otel-metrics`)**: Sent as efficient, binary **OTLP Protobuf**.
      * **Host Logs (`raw-host-logs`)**: Sent as human-readable **OTLP JSON**.

2.  **Custom Python Collector**: A custom Python service is used to collect specialized data like detailed query analytics from `pg_stat_statements`. This provides maximum flexibility for capturing non-standard telemetry.

      * **DB Logs (`raw-logs`)**: Sent as a **custom JSON** structure.
      * **Query Analytics (`raw-queries`)**: Also sent as a **custom JSON** structure.

The `processor` service is designed to handle both OTLP and custom JSON formats seamlessly.

## Data Collected

The platform collects the following types of telemetry data:

  - **PostgreSQL Metrics**: Database-level metrics collected via OpenTelemetry, including block reads, commits, database size, active connections, and more.
  - **PostgreSQL Logs**: Custom log events from the database, such as connection stats and deadlocks.
  - **PostgreSQL Queries**: Detailed query performance analytics from `pg_stat_statements`.
  - **Host Metrics & Logs**: System-level metrics (CPU, memory, disk, network) and syslog messages from the database host, collected via OpenTelemetry.

## Quick Start

### 1\. Start Data Collection & Processing

```bash
# Start the entire data pipeline (ingestion and processing)
cd ingest
make up

cd ../processor
docker-compose up -d --build
```

### 2\. Verify Data Flow

```bash
# Check that all services are healthy
cd ingest
make health

# Check the processor logs to see data being consumed and exported
cd ../processor
docker-compose logs -f
```

### 3\. Query the Data

Once data has been processed and stored in VAST DB, you can query it.

```bash
# Configure your VAST DB connection in query/.env
cd query
pip install -r requirements.txt
python querier.py
```

## Projects

  - **[ingest/](./ingest/)** - The data collection layer that monitors data sources and publishes to Kafka.
  - **[library/](./library/)** - The core Python library for processing and modeling observability data.
  - **[processor/](./processor/)** - A Kafka consumer that uses the `library` to process and store telemetry in VAST DB.
  - **[query/](./query/)** - Example scripts for querying processed data from VAST DB.

## License

Apache License 2.0 - See LICENSE file.