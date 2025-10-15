# API Reference

## Processors

### QueriesProcessor

```python
processor = QueriesProcessor()
processed = processor.process(raw_query)
```

### LogsProcessor

```python
processor = LogsProcessor()
processed = processor.process(raw_log)
```

## Exporters

### VASTExporter

```python
exporter = VASTExporter(host="...", port=5432, ...)
await exporter.connect()
await exporter.export_queries([...])
```

See full API documentation in project artifacts.
