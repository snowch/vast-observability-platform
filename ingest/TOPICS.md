# Kafka Topics Documentation

This document describes all Kafka topics produced by the Database Observability Collection Layer.

**Kafka Broker**: `kafka-ingestion:9092` (internal) / `localhost:9093` (external)

---

## Topic Overview

| Topic | Producer | Format | Frequency | Purpose |
|-------|----------|--------|-----------|---------|
| `otel-metrics` | OTel Collector | OTLP Proto | 30s | Database & host metrics |
| `raw-logs` | Python Collector | JSON | 30s | Database log events |
| `raw-queries` | Python Collector | JSON | 30s | Query performance analytics |

---

## 1. otel-metrics

### Overview
- **Producer**: OpenTelemetry Collector
- **Format**: OTLP (OpenTelemetry Protocol) - Protocol Buffers
- **Encoding**: Binary (protobuf)
- **Frequency**: Every 30 seconds
- **Partition Key**: `<host>:<database>`
- **Retention**: 7 days (configurable)

### Purpose
Collects time-series metrics about database performance and host system metrics using the standard OpenTelemetry protocol.

### Data Structure
```
ResourceMetrics {
  resource: {
    attributes: [
      {key: "service.name", value: "otel-collector"},
      {key: "deployment.environment", value: "development"},
      {key: "host.name", value: "postgres"},
      {key: "db.system", value: "postgresql"},
      {key: "db.name", value: "app_db"}
    ]
  },
  scopeMetrics: [
    {
      metrics: [
        {
          name: "postgresql.blocks_read",
          description: "Number of disk blocks read",
          unit: "blocks",
          gauge: {
            dataPoints: [
              {
                timeUnixNano: 1697280000000000000,
                asInt: 12345
              }
            ]
          }
        },
        // ... more metrics
      ]
    }
  ]
}
```

### Metrics Collected

#### PostgreSQL Metrics
| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `postgresql.blocks_read` | Gauge | blocks | Disk blocks read from storage |
| `postgresql.blocks_hit` | Gauge | blocks | Disk blocks found in cache |
| `postgresql.commits` | Sum | commits | Number of committed transactions |
| `postgresql.rollbacks` | Sum | rollbacks | Number of rolled back transactions |
| `postgresql.db_size` | Gauge | bytes | Total database size |
| `postgresql.backends` | Gauge | connections | Number of active connections |
| `postgresql.deadlocks` | Sum | deadlocks | Number of deadlocks detected |
| `postgresql.rows` | Sum | rows | Row operations (returned, fetched, inserted, updated, deleted) |
| `postgresql.operations` | Sum | operations | Total query operations |

#### Host Metrics
| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `system.cpu.utilization` | Gauge | percent | CPU usage percentage |
| `system.memory.usage` | Gauge | bytes | Memory usage |
| `system.memory.utilization` | Gauge | percent | Memory usage percentage |
| `system.disk.io` | Sum | bytes | Disk I/O |
| `system.network.io` | Sum | bytes | Network I/O |

### Consuming otel-metrics

#### From CLI
```bash
# View raw binary data (not human-readable)
make kafka-consume-metrics

# Better: Use Kafka UI
make kafka-ui
# Navigate to Topics → otel-metrics → Messages
```

#### From Code (Python)
```python
from aiokafka import AIOKafkaConsumer
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2

consumer = AIOKafkaConsumer(
    'otel-metrics',
    bootstrap_servers='localhost:9093',
    value_deserializer=lambda m: metrics_service_pb2.ExportMetricsServiceRequest.FromString(m)
)

async for message in consumer:
    metrics = message.value
    for resource_metric in metrics.resource_metrics:
        print(f"Resource: {resource_metric.resource.attributes}")
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                print(f"Metric: {metric.name} = {metric.gauge.data_points[0].as_int}")
```

### Derived Metrics
These can be calculated from the raw metrics:

```python
cache_hit_ratio = blocks_hit / (blocks_hit + blocks_read)
transaction_success_rate = commits / (commits + rollbacks)
avg_connections_per_db = backends / num_databases
```

---

## 2. raw-logs

### Overview
- **Producer**: Python Collector
- **Format**: JSON
- **Encoding**: UTF-8
- **Frequency**: Every 30 seconds (when events exist)
- **Partition Key**: `<host>:<database>`
- **Retention**: 30 days (configurable)

### Purpose
Captures database log events, errors, warnings, and operational events for troubleshooting and alerting.

### Data Structure

#### Schema
```json
{
  "timestamp": "ISO 8601 datetime",
  "source": "postgresql | mongodb | redis",
  "data_type": "log",
  "host": "string",
  "database": "string",
  "environment": "development | staging | production",
  "tags": {
    "log_level": "info | warning | error | critical"
  },
  "payload": {
    "event_type": "string",
    // event-specific fields
  }
}
```

#### Example Messages

**Deadlock Event:**
```json
{
  "timestamp": "2025-10-14T10:30:00.123456Z",
  "source": "postgresql",
  "data_type": "log",
  "host": "postgres-prod-1",
  "database": "app_db",
  "environment": "production",
  "tags": {
    "log_level": "warning"
  },
  "payload": {
    "event_type": "deadlocks",
    "count": 3,
    "time_window": "30s"
  }
}
```

**Connection Event:**
```json
{
  "timestamp": "2025-10-14T10:30:00.123456Z",
  "source": "postgresql",
  "data_type": "log",
  "host": "postgres-prod-1",
  "database": "app_db",
  "environment": "production",
  "tags": {
    "log_level": "info"
  },
  "payload": {
    "event_type": "connection",
    "action": "opened",
    "user": "app_user",
    "client_addr": "172.18.0.5"
  }
}
```

**Error Event:**
```json
{
  "timestamp": "2025-10-14T10:30:00.123456Z",
  "source": "postgresql",
  "data_type": "log",
  "host": "postgres-prod-1",
  "database": "app_db",
  "environment": "production",
  "tags": {
    "log_level": "error"
  },
  "payload": {
    "event_type": "query_error",
    "error_code": "42P01",
    "error_message": "relation \"nonexistent_table\" does not exist",
    "query": "SELECT * FROM nonexistent_table"
  }
}
```

### Event Types
- `deadlocks` - Deadlock occurrences
- `connection` - Connection open/close events
- `checkpoint` - Database checkpoint events
- `replication_lag` - Replication lag warnings
- `vacuum` - Vacuum operation events
- `query_error` - Query execution errors
- `authentication_failure` - Failed login attempts

### Consuming raw-logs

#### From CLI
```bash
make kafka-consume-logs
```

#### From Code (Python)
```python
from aiokafka import AIOKafkaConsumer
import json

consumer = AIOKafkaConsumer(
    'raw-logs',
    bootstrap_servers='localhost:9093',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

async for message in consumer:
    log_event = message.value
    
    if log_event['tags']['log_level'] == 'error':
        print(f"ERROR on {log_event['host']}: {log_event['payload']}")
    
    if log_event['payload'].get('event_type') == 'deadlocks':
        print(f"DEADLOCK detected: {log_event['payload']['count']} occurrences")
```

---

## 3. raw-queries

### Overview
- **Producer**: Python Collector
- **Format**: JSON
- **Encoding**: UTF-8
- **Frequency**: Every 30 seconds
- **Partition Key**: `<host>:<database>`
- **Retention**: 90 days (configurable)

### Purpose
Provides detailed query performance analytics from pg_stat_statements for identifying slow queries, optimizing indexes, and capacity planning.

### Data Structure

#### Schema
```json
{
  "timestamp": "ISO 8601 datetime",
  "source": "postgresql | mongodb | redis",
  "data_type": "query",
  "host": "string",
  "database": "string",
  "environment": "development | staging | production",
  "tags": {},
  "payload": {
    "queryid": "string",
    "query": "string",
    "calls": "integer",
    "total_time_ms": "float",
    "mean_time_ms": "float",
    "min_time_ms": "float",
    "max_time_ms": "float",
    "stddev_time_ms": "float",
    "rows": "integer",
    "cache_hit_ratio": "float"
  }
}
```

#### Example Message

**Slow Query:**
```json
{
  "timestamp": "2025-10-14T10:30:00.123456Z",
  "source": "postgresql",
  "data_type": "query",
  "host": "postgres-prod-1",
  "database": "app_db",
  "environment": "production",
  "tags": {},
  "payload": {
    "queryid": "1234567890",
    "query": "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.created_at > $1 GROUP BY u.id ORDER BY COUNT(o.id) DESC",
    "calls": 1523,
    "total_time_ms": 45123.45,
    "mean_time_ms": 29.63,
    "min_time_ms": 12.34,
    "max_time_ms": 234.56,
    "stddev_time_ms": 15.23,
    "rows": 15230,
    "cache_hit_ratio": 0.87,
    "shared_blks_hit": 12000,
    "shared_blks_read": 1800
  }
}
```

**Fast Query:**
```json
{
  "timestamp": "2025-10-14T10:30:00.123456Z",
  "source": "postgresql",
  "data_type": "query",
  "host": "postgres-prod-1",
  "database": "app_db",
  "environment": "production",
  "tags": {},
  "payload": {
    "queryid": "9876543210",
    "query": "SELECT * FROM users WHERE id = $1",
    "calls": 45678,
    "total_time_ms": 2345.67,
    "mean_time_ms": 0.05,
    "min_time_ms": 0.02,
    "max_time_ms": 1.23,
    "stddev_time_ms": 0.08,
    "rows": 45678,
    "cache_hit_ratio": 0.99
  }
}
```

### Payload Fields Explained

| Field | Description | Units |
|-------|-------------|-------|
| `queryid` | Unique identifier for the query | string |
| `query` | Query text (truncated to 500 chars) | string |
| `calls` | Number of times executed | count |
| `total_time_ms` | Total execution time across all calls | milliseconds |
| `mean_time_ms` | Average execution time per call | milliseconds |
| `min_time_ms` | Fastest execution time | milliseconds |
| `max_time_ms` | Slowest execution time | milliseconds |
| `stddev_time_ms` | Standard deviation of execution times | milliseconds |
| `rows` | Total rows returned/affected | count |
| `cache_hit_ratio` | Percentage of data served from cache | 0.0 - 1.0 |
| `shared_blks_hit` | Blocks read from cache | count |
| `shared_blks_read` | Blocks read from disk | count |

### Consuming raw-queries

#### From CLI
```bash
make kafka-consume-queries
```

#### From Code (Python)
```python
from aiokafka import AIOKafkaConsumer
import json

consumer = AIOKafkaConsumer(
    'raw-queries',
    bootstrap_servers='localhost:9093',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

async for message in consumer:
    query_data = message.value
    payload = query_data['payload']
    
    # Identify slow queries
    if payload['mean_time_ms'] > 100:  # >100ms average
        print(f"SLOW QUERY on {query_data['host']}:")
        print(f"  Query: {payload['query'][:100]}...")
        print(f"  Mean time: {payload['mean_time_ms']:.2f}ms")
        print(f"  Calls: {payload['calls']}")
        print(f"  Cache hit ratio: {payload['cache_hit_ratio']:.2%}")
    
    # Identify high-volume queries
    if payload['calls'] > 10000:
        print(f"HIGH VOLUME query: {payload['calls']} calls")
```

### Use Cases

1. **Slow Query Detection**
   ```python
   queries_over_100ms = filter(lambda q: q['payload']['mean_time_ms'] > 100, messages)
   ```

2. **Cache Hit Optimization**
   ```python
   poor_cache_queries = filter(lambda q: q['payload']['cache_hit_ratio'] < 0.8, messages)
   ```

3. **Query Volume Analysis**
   ```python
   top_10_by_calls = sorted(messages, key=lambda q: q['payload']['calls'], reverse=True)[:10]
   ```

4. **Performance Regression Detection**
   ```python
   # Compare mean_time_ms over time windows
   if current_mean_time > historical_mean_time * 1.5:
       alert("Query performance degraded by 50%")
   ```

---

## Consumer Implementations

### Python Consumer (aiokafka)
```python
from aiokafka import AIOKafkaConsumer
import json
import asyncio

async def consume_all_topics():
    consumer = AIOKafkaConsumer(
        'raw-logs',
        'raw-queries',
        bootstrap_servers='localhost:9093',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='observability-processor'
    )
    
    await consumer.start()
    try:
        async for message in consumer:
            print(f"Topic: {message.topic}")
            print(f"Key: {message.key.decode('utf-8')}")
            print(f"Value: {message.value}")
            print("---")
    finally:
        await consumer.stop()

asyncio.run(consume_all_topics())
```

### Kafka Streams (Java)
```java
Properties props = new Properties();
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "db-observability-processor");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9093");

StreamsBuilder builder = new StreamsBuilder();

// Consume raw-queries
KStream<String, JsonNode> queries = builder.stream("raw-queries");

queries
    .filter((key, value) -> value.get("payload").get("mean_time_ms").asDouble() > 100)
    .to("slow-queries");

KafkaStreams streams = new KafkaStreams(builder.build(), props);
streams.start();
```

---

## Data Volumes

### Expected Message Rates

| Topic | Messages/min | Messages/hour | Daily Volume |
|-------|--------------|---------------|--------------|
| `otel-metrics` | 2 per DB | 120 per DB | ~3K per DB |
| `raw-logs` | 0-10 per DB | 0-600 per DB | Variable |
| `raw-queries` | 2 per DB | 120 per DB | ~3K per DB |

**For 100 databases:**
- Total messages/hour: ~24,000
- Total messages/day: ~600,000

### Storage Requirements

| Topic | Msg Size | Daily Volume (100 DBs) | Compressed |
|-------|----------|------------------------|------------|
| `otel-metrics` | ~2 KB | ~600 MB | ~60 MB |
| `raw-logs` | ~500 B | ~150 MB | ~30 MB |
| `raw-queries` | ~1 KB | ~300 MB | ~60 MB |
| **Total** | - | **~1 GB** | **~150 MB** |

---

## Monitoring Topics

### Check Topic Existence
```bash
make kafka-topics
```

### Check Consumer Lag
```bash
docker compose exec kafka-ingestion kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group <your-consumer-group> \
  --describe
```

### View Topic Configuration
```bash
docker compose exec kafka-ingestion kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic otel-metrics
```

---

## Next Steps: Processing Layer

This collection layer publishes **raw, unprocessed data**. The separate **`vastdb-processor`** project will:

1. **Consume** from these topics
2. **Process**: Normalize, enrich, aggregate
3. **Publish** to output topics:
   - `processed-metrics`
   - `processed-logs`
   - `processed-queries`
   - `alerts`
4. **Store** in VAST Database for long-term analytics

---

## Troubleshooting

### No Messages in Topics
```bash
# Check collectors are running
make health

# Check collector logs
make logs-otel
make logs-python

# Verify pg_stat_statements is enabled
make check-pg-stats
```

### Messages Are Binary/Unreadable
- `otel-metrics` topic uses Protocol Buffers (binary format)
- Use Kafka UI or deserialize with OTLP libraries
- `raw-logs` and `raw-queries` are human-readable JSON

### Consumer Can't Deserialize
- Ensure you're using correct deserializer for each topic
- `otel-metrics`: Protocol Buffers
- `raw-logs`, `raw-queries`: JSON

---

## References

- [OpenTelemetry Protocol Specification](https://opentelemetry.io/docs/specs/otlp/)
- [PostgreSQL pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Kafka Consumer API](https://kafka.apache.org/documentation/#consumerapi)