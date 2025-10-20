# vastdb-observability

Python library for processing database observability telemetry and storing it in VAST Database.

## Quick Start

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Install the library in editable mode
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your VAST Database credentials

# Run tests
python -m pytest tests/test_processors.py -v

# Run example
python examples/simple_usage.py
```

## Installation

```bash
# For production use
pip install -e .

# For development (includes testing tools)
pip install -e ".[dev]"
```

## Usage

The library now uses an entity-centric model where events and metrics are linked to a monitored `Entity`.

```python
from vastdb_observability import QueriesProcessor, VASTExporter, Entity
from vastdb_observability.config import ProcessorConfig
from datetime import datetime

# Load configuration from .env file
config = ProcessorConfig()

# Initialize the exporter
exporter = VASTExporter(
    endpoint=config.vast_endpoint,
    access_key=config.vast_access_key,
    secret_key=config.vast_secret_key,
    bucket_name=config.vast_bucket
)

# Initialize a processor
queries_processor = QueriesProcessor()

# Process a raw message
raw_query = {"host": "postgres", ...}  # Raw data from Kafka
processed_event = queries_processor.process(raw_query)

# Create an entity for the monitored host
entity = Entity(
    entity_id=processed_event.entity_id,
    entity_type="database_host",
    first_seen=datetime.utcnow(),
    last_seen=datetime.utcnow(),
    attributes={"source_system": "postgresql"}
)

# Export the processed data
await exporter.connect()
await exporter.export_events([processed_event])
await exporter.export_entities([entity])
await exporter.disconnect()
```

## Documentation

See `docs/` directory for detailed documentation:

- `ARCHITECTURE.md` - System architecture
- `API.md` - API reference
- `SETUP.md` - Setup guide

## Testing

```bash
# Run all tests
python -m pytest tests/test_processors.py -v

# Run tests with coverage
python -m pytest --cov=vastdb_observability tests/

# Run with verbose output
python -m pytest tests/test_processors.py -vv
```

## Development

```bash
# Format code
black vastdb_observability/ tests/ examples/

# Lint code
ruff check vastdb_observability/

# Type check
mypy vastdb_observability/
```

## License

Apache License 2.0
