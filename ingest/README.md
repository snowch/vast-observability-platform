# Database Observability Platform - Collection Layer

**Scope**: This project implements the **data collection layer only**. It monitors databases and publishes raw telemetry to Kafka topics for downstream processing.

**What This Does**: ✅ Agentless database monitoring, ✅ Raw data collection, ✅ Kafka publishing  
**What This Doesn't Do**: ❌ Data processing, ❌ Data enrichment, ❌ Storage, ❌ Dashboards

---

## Quick Start

```bash
# Start all services
make up

# Check health (wait 30-60s for Kafka to be ready)
make health

# View data flowing through Kafka
make kafka-topics          # List topics
make kafka-consume-metrics # See OTel metrics
make kafka-consume-queries # See query analytics

# Debug if needed
make debug
```

---

## Architecture Overview

```
┌──────────────┐
│  PostgreSQL  │
└──────┬───────┘
       │
       ├─── Read-only connection #1 ───> [OTel Collector]
       │    (metrics via pg_stat_*)           │
       │                                      ├─> [otel-metrics]
       │
       └─── Read-only connection #2 ───> [Python Collector]
            (logs/queries via                  │
             pg_stat_statements)               ├─> [raw-logs]
                                               └─> [raw-queries]
```

```
┌──────────────┐
│ Centos Host  │
└──────┬───────┘
       ├─── Host Metrics Receiver ───> [OTel Collector]
       │    (CPU, memory, disk, net)          │
       │                                      ├─> [otel-metrics]
       │
       └─── Syslog Receiver ──────────> [OTel Collector]
            (syslog messages)                 │
                                              ├─> [raw-host-logs]
```

The project is not entirely consistent in its use of the OTEL protocol. This is done intentionally to demonstrate two alternative approaches for collecting and transmitting observability data.

Here’s a breakdown of the two methods used in the platform:

1. Standard OpenTelemetry (OTLP) Approach

This method uses the standard OpenTelemetry Collector for gathering metrics and system logs. It relies on established OTLP formats, which ensures interoperability with the wider OpenTelemetry ecosystem.

    Metrics (otel-metrics topic): The OTEL Collector gathers metrics from PostgreSQL and the host system. It then exports them to Kafka using the standard binary OTLP protobuf format. This is a highly efficient, compressed format ideal for high-volume metric data.

    Host Logs (raw-host-logs topic): System logs are captured via the OTEL Collector's syslog receiver and exported to Kafka in OTLP JSON format. While still following the OTLP structure, this format is human-readable, which can be useful for debugging.

2. Custom JSON Approach

This method uses a custom-built Python application to collect more specialized data, such as detailed query analytics. This approach offers greater flexibility in defining the exact structure of the data being sent.

    Database Logs (raw-logs topic): The Python collector gathers specific log events like deadlocks and connection stats from PostgreSQL.

    Query Analytics (raw-queries topic): Detailed query performance data is collected from pg_stat_statements.

Both of these are sent to Kafka as custom JSON objects, not in the OTLP format. This allows for a schema tailored specifically to the needs of the downstream processing and analysis layers.

By implementing both methods, the project effectively showcases the trade-off between the standardization and interoperability of the OTLP protocol versus the flexibility and simplicity of a custom JSON implementation.

**Collection Methods:**
- **OTel Collector**: Collects metrics from two sources:
  - **PostgreSQL**: Database metrics via the PostgreSQL receiver (30s intervals).
  - **Host (Centos)**: System-level metrics (CPU, memory, disk, network) via the Host Metrics receiver.
- **Python Collector**: Logs and query analytics via `pg_stat_statements` (30s intervals).
- **Load Simulator**: Generates test database traffic.

**Data Flow:**
1. Collectors connect to databases (read-only, agentless)
2. Collectors publish raw telemetry to Kafka
3. **Downstream processor** (separate project) consumes, enriches, and stores data

---

## Kafka Topics

All topics are on `kafka-ingestion` (localhost:9092)

### 1. `otel-metrics` (formerly raw-metrics)

**Source**: OpenTelemetry Collector  
**Format**: OTLP (Protocol Buffers)  
**Frequency**: Every 30 seconds  
**Content**: Database and host system metrics.

**Metrics Included:**
- **PostgreSQL Metrics**:
  - `postgresql.blocks_read` - Disk block reads
  - `postgresql.commits` - Transaction commits
  - `postgresql.db_size` - Database size in bytes
  - `postgresql.backends` - Active connections
  - `postgresql.deadlocks` - Deadlock count
  - `postgresql.rows` - Row operations
  - `postgresql.operations` - Query operations
- **Host Metrics (Centos)**:
  - System-level metrics including CPU, memory, disk, and network usage.

**Key Schema:**
```
key: <host>:<database>
value: OTLP ResourceMetrics proto
```

**Consumption:**
```bash
make kafka-consume-metrics
```

---

### 2. `raw-logs` 

**Source**: Python Collector  
**Format**: JSON  
**Frequency**: Every 30 seconds (if events present)  
**Content**: Database log events and errors

**Example Message:**
```json
{
  "timestamp": "2025-10-14T10:30:00.000Z",
  "source": "postgresql",
  "data_type": "log",
  "host": "postgres",
  "database": "app_db",
  "environment": "development",
  "tags": {
    "log_level": "warning"
  },
  "payload": {
    "event_type": "deadlocks",
    "count": 2
  }
}
```

**Key Schema:**
```
key: <host>:<database>
value: JSON ObservabilityData
```

**Consumption:**
```bash
make kafka-consume-logs
```

---

### 3. `raw-queries`

**Source**: Python Collector  
**Format**: JSON  
**Frequency**: Every 30 seconds  
**Content**: Query performance analytics from pg_stat_statements

**Example Message:**
```json
{
  "timestamp": "2025-10-14T10:30:00.000Z",
  "source": "postgresql",
  "data_type": "query",
  "host": "postgres",
  "database": "app_db",
  "environment": "development",
  "tags": {},
  "payload": {
    "queryid": "1234567890",
    "query": "SELECT * FROM users WHERE...",
    "calls": 1523,
    "total_time_ms": 45123.45,
    "mean_time_ms": 29.63
  }
}
```

**Key Schema:**
```
key: <host>:<database>
value: JSON ObservabilityData
```

**Consumption:**
```bash
make kafka-consume-queries
```

---

### 4. `raw-host-logs`

**Source**: OpenTelemetry Collector (from syslog)  
**Format**: JSON  
**Frequency**: Real-time  
**Content**: System logs from the CentOS host.

**Consumption:**

```bash
make kafka-consume-host-logs
```

---

## Services

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| PostgreSQL | 5432 | Data source | `make shell-pg` |
| Kafka | 9092 | Message bus (internal) | `make kafka-topics` |
| Kafka | 9093 | Message bus (external) | - |
| Kafka UI | 8080 | Web UI | http://localhost:8080 |
| OTel Collector | 13133 | Health endpoint | http://localhost:13133/health |
| Python Collector | - | Background service | `make logs-python` |
| Load Simulator | - | Traffic generator | `make logs-simulator` |

---

## Available Commands

### Service Management
```bash
make up               # Start all services
make down             # Stop all services
make restart          # Restart everything
make clean            # Stop and remove volumes
make ps               # Show container status
make health           # Health check all services
```

### Debugging
```bash
make debug            # Show comprehensive debug info
make logs             # Tail all logs
make logs-otel        # OTel Collector logs
make logs-python      # Python Collector logs
make logs-simulator   # Load Simulator logs
make logs-postgres    # PostgreSQL logs
make logs-kafka       # Kafka logs
```

### Kafka Operations
```bash
make kafka-topics            # List all topics
make kafka-consume-metrics   # View metrics data
make kafka-consume-logs      # View log data
make kafka-consume-queries   # View query analytics data
make kafka-consume-host-logs # View host log data
make kafka-ui                # Open Kafka UI in browser
```

### Database Operations
```bash
make shell-pg         # Open PostgreSQL shell
make check-pg-stats   # Verify pg_stat_statements
```

### Load Simulator
```bash
make simulator-logs   # View simulator statistics
make stop-simulator   # Stop traffic generation
make start-simulator  # Resume traffic generation
```

### Quick Fixes
```bash
make fix-permissions      # Fix file permissions
make rebuild-collectors   # Rebuild collector images
make fix-and-restart      # Apply all fixes
```

---

## Data Volumes

**Important**: PostgreSQL data persists across restarts in the `postgres_data` volume.

To completely reset:
```bash
make clean  # Removes all volumes including database
```

---

## Monitoring Data Flow

### 1. Check Services Are Running
```bash
make health
# Expected: All services show ✓ Healthy/Running
```

### 2. Verify Topics Exist
```bash
make kafka-topics
# Expected output:
# otel-metrics
# raw-logs
# raw-queries
```

### 3. View Live Data
```bash
# Terminal 1: Watch metrics
make kafka-consume-metrics

# Terminal 2: Watch queries
make kafka-consume-queries

# Terminal 3: Watch logs
make kafka-consume-logs
```

### 4. Check Kafka UI
```bash
make kafka-ui
# Browse to http://localhost:8080
# Navigate to Topics → Select topic → Messages
```

---

## Configuration

### Database Connection
Default PostgreSQL credentials (configured in docker-compose.yml):
- **Host**: postgres (internal) / localhost:5432 (external)
- **Database**: app_db
- **Application User**: app_user / app_password
- **Monitor User**: monitor_user / monitor_password (read-only)

### Collection Intervals
- **OTel Metrics**: 30 seconds (configurable in otel-collector-config.yaml)
- **Python Collector**: 30 seconds (set via `COLLECTION_INTERVAL` env var)

### Load Simulator Settings
Configure via environment variables in docker-compose.yml:
- `QUERY_RATE`: Queries per second (default: 10)
- `SLOW_QUERY_PROBABILITY`: Chance of slow query (default: 0.1 = 10%)
- `WRITE_PROBABILITY`: Chance of write operation (default: 0.3 = 30%)

---

## Troubleshooting

### Services Won't Start
```bash
make debug           # See what's failing
make fix-and-restart # Apply common fixes
```

### No Data in Kafka Topics
```bash
# 1. Check collectors are running
make ps

# 2. Check collector logs
make logs-otel
make logs-python

# 3. Verify PostgreSQL is accessible
make shell-pg
# Run: SELECT 1;

# 4. Check pg_stat_statements
make check-pg-stats
```

### Permission Errors
```bash
make fix-permissions  # Fix config file permissions
make rebuild-collectors
```

### Kafka Takes Long to Start
Kafka can take 30-60 seconds to become ready. Wait and retry:
```bash
sleep 30
make health
```

See **FIXES.md** for detailed troubleshooting guide.

---

## Project Scope & Limitations

### ✅ What This Project Does
- Monitors PostgreSQL databases (agentless, read-only)
- Collects metrics via OpenTelemetry
- Collects logs and query analytics via Python
- Publishes raw telemetry to Kafka topics
- Generates test database load

### ❌ What This Project Does NOT Do
- **Data Processing**: No normalization, enrichment, or aggregation
- **Data Storage**: No VAST Database or long-term storage
- **Visualization**: No dashboards or Superset
- **Alerting**: No alert generation or notification
- **Multi-Database Support**: Only PostgreSQL implemented (MongoDB/Redis planned)

**Next Step**: The separate **`vastdb-processor`** project will:
- Consume from these topics
- Process and enrich data
- Publish to output Kafka topics
- Store in VAST Database
- Enable visualization and analytics

---

## Data Schema Reference

### ObservabilityData (Python Collector)
```python
{
  "timestamp": "ISO 8601 datetime",
  "source": "postgresql | mongodb | redis",
  "data_type": "log | query | metric",
  "host": "database hostname",
  "database": "database name",
  "environment": "development | staging | production",
  "tags": {"key": "value"},  # Optional metadata
  "payload": {/* type-specific data */}
}
```

### OTLP Metrics (OTel Collector)
Standard OpenTelemetry Protocol Buffers format.  
See: https://opentelemetry.io/docs/specs/otlp/

---

## Development

### Adding a New Database to Monitor
1. Add database service to docker-compose.yml
2. Update OTel Collector config (otel-collector-config.yaml)
3. Add Python collector for logs/queries (if needed)
4. Restart: `make restart`

### Scaling Collectors
```bash
# Run multiple Python collector instances
make scale-collectors
# Enter: 3
```

### Testing Without Load Simulator
```bash
make stop-simulator
# Manually run queries via: make shell-pg
```

---

## Architecture Documentation

- **Solution Architecture**: See `absa_observability.md`
- **Visual Diagram**: See `absa_eraser.io.txt`
- **Troubleshooting**: See `FIXES.md`

---

## License

Apache License 2.0 - See LICENSE file

---

## Support

For issues or questions:
1. Run `make debug > debug.log` and review the output
2. Check FIXES.md for common issues
3. Review service logs: `make logs-<service>`

**Remember**: This is the collection layer only. For data processing, enrichment, and storage, see the separate `vastdb-processor` project.
