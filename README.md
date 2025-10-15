# VAST Observability Platform

Complete database observability platform for collecting, processing, and analyzing database telemetry.

## Project Structure
```
vast-observability-platform/
├── ingest/                  # Data collection layer
│   ├── docker-compose.yml   # PostgreSQL, Kafka, Collectors
│   ├── Makefile             # Service management
│   └── ...
└── library/                 # Data processing library
    ├── vastdb_observability/ # Python package
    ├── tests/               # Tests with real data
    └── ...
```

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
pip install -r requirements.txt
pytest tests/test_integration.py -v
```

## Projects

- **[ingest/](./ingest/)** - Collection layer that monitors databases and publishes to Kafka
- **[library/](./library/)** - Python library for processing and storing observability data

## Documentation

- [Ingestion Layer README](./ingest/README.md)
- [Library README](./library/README.md)
- [Kafka Topics Documentation](./ingest/TOPICS.md)
- [Project Scope](./ingest/PROJECT_SCOPE.md)

## License

Apache License 2.0 - See LICENSE file
