# VAST Observability Platform

Complete database observability platform for collecting, processing, and analyzing database telemetry.

## Project Structure
```
vast-observability-platform/
├── ingest/                  # Data collection layer
│   ├── docker-compose.yml   # PostgreSQL, Kafka, Collectors
│   ├── Makefile             # Service management
│   └── ...
├── library/                 # Data processing library
│   ├── vastdb_observability/ # Python package for processing telemetry
│   └── ...
├── processor/               # Kafka consumer that processes and stores data
│   ├── docker-compose.yml   # Runs the processor service
│   └── ...
└── query/                   # Scripts for querying data from VAST DB
    └── ...
```

## Data Collected

The platform collects the following types of telemetry data:

- **PostgreSQL Metrics**: Database-level metrics collected via an OpenTelemetry collector, including:
  - `postgresql.blocks_read`, `postgresql.commits`, `postgresql.db_size`, `postgresql.backends`, `postgresql.deadlocks`, `postgresql.rows`, `postgresql.operations`.
- **PostgreSQL Logs**: Raw log events and errors from the database.
- **PostgreSQL Queries**: Query performance and analytics from `pg_stat_statements`.
- **Host Metrics**: System-level metrics for the database host (Centos), including CPU, memory, disk, and network usage, collected via OpenTelemetry.

## Quick Start

### 1. Start Data Collection
```bash
cd ingest
make up
make health
```

### 2. Collect Test Data
```bash
cd ingest
make setup-library-tests
make copy-test-data-to-library
```

### 3. Run Library Tests
```bash
cd library
pip install -r requirements-dev.txt
pip install -e .
python -m pytest tests/test_processors.py -v
```

## Projects

- **[ingest/](./ingest/)** - Collection layer that monitors databases and publishes to Kafka.
- **[library/](./library/)** - Python library for processing and storing observability data.
- **[processor/](./processor/)** - Kafka consumer that uses the library to process and store data.
- **[query/](./query/)** - Example scripts for querying the processed data from VAST DB.

## Documentation

- [Ingestion Layer](./ingest/README.md)
- [Processing Library](./library/README.md)
- [Kafka Processor](./processor/README.md)
- [Kafka Topics Documentation](./ingest/TOPICS.md)
- [Project Scope](./ingest/PROJECT_SCOPE.md)

## License

Apache License 2.0 - See LICENSE file
