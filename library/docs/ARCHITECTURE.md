# Architecture

This library processes raw telemetry data and stores it in VAST Database.

## Components

- **Processors**: Normalize and enrich data
- **Exporters**: Write to VAST Database
- **Models**: Data structures

## Data Flow

```
Raw Data → Processor → Exporter → VAST Database
```

See full documentation in project artifacts.
