-- VAST Database Schema for Observability Data

CREATE SCHEMA IF NOT EXISTS observability;
SET search_path TO observability;

-- Metrics table
CREATE TABLE IF NOT EXISTS db_metrics (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_type VARCHAR(50),
    unit VARCHAR(50),
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON db_metrics(timestamp DESC);
CREATE INDEX idx_metrics_source_host ON db_metrics(source, host, database_name);
CREATE INDEX idx_metrics_name ON db_metrics(metric_name);

-- Logs table
CREATE TABLE IF NOT EXISTS db_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    log_level VARCHAR(20),
    event_type VARCHAR(100),
    message TEXT,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_timestamp ON db_logs(timestamp DESC);
CREATE INDEX idx_logs_source_host ON db_logs(source, host, database_name);
CREATE INDEX idx_logs_level ON db_logs(log_level);

-- Queries table
CREATE TABLE IF NOT EXISTS db_queries (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),
    query_id VARCHAR(255) NOT NULL,
    query_text TEXT,
    query_hash VARCHAR(64),
    calls BIGINT,
    total_time_ms DOUBLE PRECISION,
    mean_time_ms DOUBLE PRECISION,
    min_time_ms DOUBLE PRECISION,
    max_time_ms DOUBLE PRECISION,
    stddev_time_ms DOUBLE PRECISION,
    rows_affected BIGINT,
    cache_hit_ratio DOUBLE PRECISION,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_timestamp ON db_queries(timestamp DESC);
CREATE INDEX idx_queries_source_host ON db_queries(source, host, database_name);
CREATE INDEX idx_queries_hash ON db_queries(query_hash);
CREATE INDEX idx_queries_mean_time ON db_queries(mean_time_ms DESC);
