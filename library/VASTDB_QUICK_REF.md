# VAST Database Quick Reference

## Table Schemas

### db_metrics
```
Sorting Keys: [timestamp, host, database_name, metric_name]

Columns (in order):
  timestamp         TIMESTAMP (µs)  ← Sorting key #1
  host              STRING          ← Sorting key #2
  database_name     STRING          ← Sorting key #3
  metric_name       STRING          ← Sorting key #4
  source            STRING
  environment       STRING
  metric_value      DOUBLE
  metric_type       STRING
  unit              STRING
  tags              STRING (JSON)
  metadata          STRING (JSON)
  created_at        TIMESTAMP (µs)
  id                STRING (UUID)
```

### db_logs
```
Sorting Keys: [timestamp, host, database_name, log_level]

Columns (in order):
  timestamp         TIMESTAMP (µs)  ← Sorting key #1
  host              STRING          ← Sorting key #2
  database_name     STRING          ← Sorting key #3
  log_level         STRING          ← Sorting key #4
  source            STRING
  environment       STRING
  event_type        STRING
  message           STRING
  tags              STRING (JSON)
  metadata          STRING (JSON)
  created_at        TIMESTAMP (µs)
  id                STRING (UUID)
```

### db_queries
```
Sorting Keys: [timestamp, host, database_name, mean_time_ms]

Columns (in order):
  timestamp         TIMESTAMP (µs)  ← Sorting key #1
  host              STRING          ← Sorting key #2
  database_name     STRING          ← Sorting key #3
  mean_time_ms      DOUBLE          ← Sorting key #4
  source            STRING
  environment       STRING
  query_id          STRING
  query_text        STRING
  query_hash        STRING
  calls             INT64
  total_time_ms     DOUBLE
  min_time_ms       DOUBLE
  max_time_ms       DOUBLE
  stddev_time_ms    DOUBLE
  rows_affected     INT64
  cache_hit_ratio   DOUBLE
  tags              STRING (JSON)
  metadata          STRING (JSON)
  created_at        TIMESTAMP (µs)
  id                STRING (UUID)
```

## Arrow Type Mappings

| PostgreSQL | VAST/Arrow | Notes |
|------------|-----------|-------|
| UUID | STRING | Store as string |
| VARCHAR(n) | STRING | No length limit |
| TEXT | STRING | No length limit |
| BIGINT | INT64 | 64-bit integer |
| INTEGER | INT32 | 32-bit integer |
| DOUBLE PRECISION | DOUBLE | 64-bit float |
| FLOAT | FLOAT | 32-bit float |
| BOOLEAN | BOOL | True/False |
| JSONB | STRING | Serialize JSON |
| TIMESTAMP | TIMESTAMP | Microseconds |

## Python Code Examples

### Connection
```python
from vastdb import connect

session = connect(
    endpoint="http://vast.example.com:5432",
    access="access-key",
    secret="secret-key"
)

database = session.database("observability")
schema = database.schema("observability")
```

### Creating a Table
```python
import pyarrow as pa

schema = pa.schema([
    ('timestamp', pa.timestamp('us')),
    ('host', pa.string()),
    ('database_name', pa.string()),
    ('metric_name', pa.string()),
    # ... more columns
])

table = db_schema.create_table(
    'db_metrics',
    schema,
    sorting_key=['timestamp', 'host', 'database_name', 'metric_name']
)
```

### Inserting Data
```python
import pyarrow as pa
import json
from datetime import datetime

def timestamp_to_us(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000)

# Prepare data
data = {
    'timestamp': pa.array([timestamp_to_us(datetime.now())], 
                         type=pa.timestamp('us')),
    'host': pa.array(['prod-db-1']),
    'database_name': pa.array(['app_db']),
    'metric_name': pa.array(['postgresql.backends']),
    'metric_value': pa.array([10.0]),
    'tags': pa.array([json.dumps({"env": "prod"})]),
    # ... more columns
}

batch = pa.RecordBatch.from_pydict(data)
table.insert(batch)
```

### Querying Data
```python
# Query using PyArrow
results = table.select(
    columns=['timestamp', 'host', 'metric_value'],
    filter="timestamp > '2025-01-01'"
)

# Convert to pandas
df = results.to_pandas()
```

## Query Optimization Cheat Sheet

### ✅ Fast Queries (Use Sorting Keys)
```sql
-- Time range (sorting key #1)
WHERE timestamp BETWEEN '2025-01-01' AND '2025-01-02'

-- Time + Host (sorting keys #1, #2)
WHERE timestamp > '2025-01-01' AND host = 'prod-db-1'

-- All sorting keys
WHERE timestamp > '2025-01-01' 
  AND host = 'prod-db-1'
  AND database_name = 'app_db'
  AND metric_name = 'postgresql.backends'

-- Slow queries (sorting key #4 on db_queries)
WHERE mean_time_ms > 1000
```

### ❌ Slow Queries (No Sorting Keys)
```sql
-- Full table scan
WHERE environment = 'production'

-- String search
WHERE query_text LIKE '%SELECT%'

-- JSON field search (stored as string)
WHERE tags LIKE '%critical%'
```

### 💡 Optimization Tips
1. Always include `timestamp` in WHERE clause when possible
2. Add `host` filter for multi-host deployments
3. Use `ORDER BY` on sorting key columns
4. Avoid `SELECT *` - specify needed columns
5. Use aggregations wisely (GROUP BY on sorting keys)

## Common Patterns

### Last 24 Hours
```sql
SELECT * FROM observability.db_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND host = 'prod-db-1';
```

### Top N Slow Queries
```sql
SELECT query_text, mean_time_ms, calls
FROM observability.db_queries
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND mean_time_ms > 1000
ORDER BY mean_time_ms DESC
LIMIT 20;
```

### Error Logs
```sql
SELECT timestamp, host, event_type, message
FROM observability.db_logs
WHERE timestamp > NOW() - INTERVAL '1 day'
  AND log_level IN ('error', 'critical')
ORDER BY timestamp DESC;
```

### Metric Aggregation
```sql
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    host,
    AVG(metric_value) as avg_value
FROM observability.db_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND metric_name = 'postgresql.backends'
GROUP BY minute, host
ORDER BY minute DESC;
```

## Troubleshooting

### Check Table Schema
```python
table = schema.table('db_metrics')
print(table.schema)
```

### List Tables
```python
tables = schema.list_tables()
print(tables)
```

### Inspect Data
```python
# Get first 10 rows
results = table.select(limit=10)
df = results.to_pandas()
print(df)
```

### Check Sorting Keys
```python
# Table properties show sorting configuration
print(table.sorting_key)
```

## Need Help?

- **Documentation**: https://support.vastdata.com/
- **Schema File**: `library/schema.sql`
- **Table Creator**: `create_vast_tables.py`
- **Exporter**: `vastdb_observability/exporters/vast.py`
- **Migration Guide**: See full migration guide document