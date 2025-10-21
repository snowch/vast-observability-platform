# VAST Observability Platform

Complete database observability platform for collecting, processing, and analyzing database telemetry.

## Project Structure

This project is a monorepo containing all services required to run the observability platform. All services are managed by the top-level `docker-compose.yml` and `Makefile`.

```

vast-observability-platform/
├── docker-compose.yml       \# ✅ Main Docker Compose file for ALL services
├── Makefile                 \# ✅ Main Makefile for managing the platform
├── .env.example             \# ✅ Master configuration file
├── ingest/                  \# Data collection layer (OTel, Python collectors, etc.)
├── library/                 \# Core Python library for data processing
├── processor/               \# Kafka consumer to process and store data in VAST DB
└── query/                   \# Scripts for querying data from VAST DB

````

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

1.  **Configure Environment**
    Copy the master configuration file. You only need to do this once.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and fill in your `VAST_ACCESS_KEY` and `VAST_SECRET_KEY`.

2.  **Start the Platform**
    This single command builds and starts all services: PostgreSQL, Kafka, the collectors, and the processor.
    ```bash
    make up
    ```

3.  **Check Platform Health**
    Wait about 60 seconds for all services to initialize, then run:
    ```bash
    make health
    ```
    You should see `✓ Healthy` or `✓ Running` for all services.

4.  **Verify Data Flow**
    * See which Kafka topics have been created: `make kafka-topics`
    * Watch the processor logs to see data being consumed and exported to VAST: `make logs-processor`
    * Open the Kafka UI to browse messages: `make kafka-ui` (http://localhost:8080)

## Projects

  - **[ingest/](./ingest/)** - The data collection layer that monitors data sources and publishes to Kafka.
  - **[library/](./library/)** - The core Python library for processing and modeling observability data.
  - **[processor/](./processor/)** - A Kafka consumer that uses the `library` to process and store telemetry in VAST DB.
  - **[query/](./query/)** - Example scripts for querying processed data from VAST DB.

## License

Apache License 2.0 - See LICENSE file.