-- VAST Database Schema for Observability Data
-- Using Arrow-compatible data types with VAST-specific optimizations
-- Reference: https://support.vastdata.com/s/article/UUID-48d0a8cf-5786-5ef3-3fa3-9c64e63a0967

-- Note: Use PyArrow Schema and vastdb.create_table() for proper table creation
-- This SQL is for documentation/reference only

-- =============================================================================
-- Metrics Table
-- =============================================================================
-- Query patterns: Filter by timestamp, host, database, metric_name
-- Sorting keys (up to 4): timestamp, host, database_name, metric_name
-- 
-- Example Python creation:
--   schema = pa.schema([
--       ('vastdb_rowid', pa.int64()),  # Optional: for row-level control
--       ('timestamp', pa.timestamp('us')),
--       ('host', pa.string()),
--       ('database_name', pa.string()),
--       ('metric_name', pa.string()),
--       ('source', pa.string()),
--       ('environment', pa.string()),
--       ('metric_value', pa.float64()),
--       ('metric_type', pa.string()),
--       ('unit', pa.string()),
--       ('tags', pa.string()),
--       ('metadata', pa.string()),
--       ('created_at', pa.timestamp('us'))
--   ])
--   table = db_schema.create_table(
--       'db_metrics',
--       schema,
--       sorting_key=['timestamp', 'host', 'database_name', 'metric_name']
--   )

CREATE TABLE observability.db_metrics (
    vastdb_rowid INT64,  -- Optional: for row-level access/control
    timestamp TIMESTAMP,  -- Sorting key 1: Primary filter (time-series queries)
    host STRING,          -- Sorting key 2: Common filter (per-host queries)
    database_name STRING, -- Sorting key 3: Common filter (per-database queries)
    metric_name STRING,   -- Sorting key 4: Metric type filter
    source STRING,
    environment STRING,
    metric_value DOUBLE,
    metric_type STRING,
    unit STRING,
    tags STRING,          -- JSON serialized as string
    metadata STRING,      -- JSON serialized as string
    created_at TIMESTAMP
);

-- =============================================================================
-- Logs Table
-- =============================================================================
-- Query patterns: Filter by timestamp, host, database, log_level/event_type
-- Sorting keys (up to 4): timestamp, host, database_name, log_level
--
-- Example Python creation:
--   schema = pa.schema([
--       ('vastdb_rowid', pa.int64()),
--       ('timestamp', pa.timestamp('us')),
--       ('host', pa.string()),
--       ('database_name', pa.string()),
--       ('log_level', pa.string()),
--       ('source', pa.string()),
--       ('environment', pa.string()),
--       ('event_type', pa.string()),
--       ('message', pa.string()),
--       ('tags', pa.string()),
--       ('metadata', pa.string()),
--       ('created_at', pa.timestamp('us'))
--   ])
--   table = db_schema.create_table(
--       'db_logs',
--       schema,
--       sorting_key=['timestamp', 'host', 'database_name', 'log_level']
--   )

CREATE TABLE observability.db_logs (
    vastdb_rowid INT64,   -- Optional: for row-level access/control
    timestamp TIMESTAMP,  -- Sorting key 1: Primary filter (time-series queries)
    host STRING,          -- Sorting key 2: Common filter (per-host queries)
    database_name STRING, -- Sorting key 3: Common filter (per-database queries)
    log_level STRING,     -- Sorting key 4: Severity filter (errors, warnings)
    source STRING,
    environment STRING,
    event_type STRING,
    message STRING,
    tags STRING,          -- JSON serialized as string
    metadata STRING,      -- JSON serialized as string
    created_at TIMESTAMP
);

-- =============================================================================
-- Queries Table
-- =============================================================================
-- Query patterns: Filter by timestamp, host, database, performance metrics
-- Sorting keys (up to 4): timestamp, host, database_name, mean_time_ms
--
-- Example Python creation:
--   schema = pa.schema([
--       ('vastdb_rowid', pa.int64()),
--       ('timestamp', pa.timestamp('us')),
--       ('host', pa.string()),
--       ('database_name', pa.string()),
--       ('mean_time_ms', pa.float64()),
--       ('source', pa.string()),
--       ('environment', pa.string()),
--       ('query_id', pa.string()),
--       ('query_text', pa.string()),
--       ('query_hash', pa.string()),
--       ('calls', pa.int64()),
--       ('total_time_ms', pa.float64()),
--       ('min_time_ms', pa.float64()),
--       ('max_time_ms', pa.float64()),
--       ('stddev_time_ms', pa.float64()),
--       ('rows_affected', pa.int64()),
--       ('cache_hit_ratio', pa.float64()),
--       ('tags', pa.string()),
--       ('metadata', pa.string()),
--       ('created_at', pa.timestamp('us'))
--   ])
--   table = db_schema.create_table(
--       'db_queries',
--       schema,
--       sorting_key=['timestamp', 'host', 'database_name', 'mean_time_ms']
--   )

CREATE TABLE observability.db_queries (
    vastdb_rowid INT64,   -- Optional: for row-level access/control
    timestamp TIMESTAMP,  -- Sorting key 1: Primary filter (time-series queries)
    host STRING,          -- Sorting key 2: Common filter (per-host queries)
    database_name STRING, -- Sorting key 3: Common filter (per-database queries)
    mean_time_ms DOUBLE,  -- Sorting key 4: Performance filter (find slow queries)
    source STRING,
    environment STRING,
    query_id STRING,
    query_text STRING,
    query_hash STRING,
    calls INT64,
    total_time_ms DOUBLE,
    min_time_ms DOUBLE,
    max_time_ms DOUBLE,
    stddev_time_ms DOUBLE,
    rows_affected INT64,
    cache_hit_ratio DOUBLE,
    tags STRING,          -- JSON serialized as string
    metadata STRING,      -- JSON serialized as string
    created_at TIMESTAMP
);

-- =============================================================================
-- Usage Notes
-- =============================================================================
--
-- 1. Sorting Keys (up to 4 columns):
--    - Optimize for your most common query patterns
--    - Order by selectivity: timestamp (time ranges) → categorical filters
--    - VAST uses these for efficient data organization and pruning
--
-- 2. Row IDs (vastdb_rowid):
--    - Auto-allocated by default (use_external_row_ids_allocation=False)
--    - User-controlled if needed (use_external_row_ids_allocation=True)
--    - Useful for: Point queries, range scans, data lineage
--    - Query example: SELECT * FROM db_metrics WHERE vastdb_rowid > 1000 AND vastdb_rowid < 2000
--
-- 3. Column Ordering:
--    - Place sorting key columns first
--    - Then frequently accessed columns
--    - Then rarely accessed columns
--    - VAST columnar storage benefits from this ordering
--
-- 4. Query Optimization Examples:
--    - Time range: WHERE timestamp BETWEEN '2025-01-01' AND '2025-01-02'
--    - Host filter: WHERE host = 'prod-db-1'
--    - Slow queries: WHERE mean_time_ms > 1000 (uses sorting key!)
--    - Combined: WHERE timestamp > '2025-01-01' AND host = 'prod-db-1' AND log_level = 'error'