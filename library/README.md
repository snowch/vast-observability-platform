# vastdb-observability

Python library for processing database observability telemetry and storing it in VAST Database.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your VAST Database credentials

# Run example
python examples/simple_usage.py
```

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from vastdb_observability import QueriesProcessor, VASTExporter

processor = QueriesProcessor()
exporter = VASTExporter(
    host="vast.example.com",
    port=5432,
    database="observability",
    username="vast_user",
    password="secure_password"
)

await exporter.connect()

raw_query = {...}  # From Kafka
processed = processor.process(raw_query)
await exporter.export_queries([processed])
```

## Documentation

See `docs/` directory for detailed documentation:

- `ARCHITECTURE.md` - System architecture
- `API.md` - API reference
- `SETUP.md` - Setup guide

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=vastdb_observability
```

## License

Apache License 2.0
