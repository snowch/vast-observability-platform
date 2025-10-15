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