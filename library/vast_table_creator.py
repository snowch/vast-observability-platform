#!/usr/bin/env python3
"""
Create VAST Database tables for observability data.

Usage:
    python create_vast_tables.py --host vast.example.com --port 5432 \\
                                  --database observability --schema observability \\
                                  --access-key YOUR_KEY --secret-key YOUR_SECRET
"""

import argparse
import pyarrow as pa
from vastdb import connect


def create_metrics_table(db_schema, use_row_ids: bool = False):
    """Create db_metrics table with optimized sorting keys."""
    
    columns = [
        ('timestamp', pa.timestamp('us')),       # Sorting key 1: Time-series queries
        ('host', pa.string()),                   # Sorting key 2: Per-host filtering
        ('database_name', pa.string()),          # Sorting key 3: Per-database filtering
        ('metric_name', pa.string()),            # Sorting key 4: Metric type filtering
        ('source', pa.string()),
        ('environment', pa.string()),
        ('metric_value', pa.float64()),
        ('metric_type', pa.string()),
        ('unit', pa.string()),
        ('tags', pa.string()),                   # JSON as string
        ('metadata', pa.string()),               # JSON as string
        ('created_at', pa.timestamp('us')),
        ('id', pa.string()),                     # UUID for deduplication
    ]
    
    # Add vastdb_rowid if requested
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))
    
    schema = pa.schema(columns)
    
    # Create table with sorting keys (up to 4 columns)
    table = db_schema.create_table(
        'db_metrics',
        schema,
        fail_if_exists=False,  # Allow recreation
        use_external_row_ids_allocation=use_row_ids,
        sorting_key=['timestamp', 'host', 'database_name', 'metric_name']
    )
    
    print(f"✓ Created table: db_metrics")
    print(f"  Sorting keys: timestamp, host, database_name, metric_name")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def create_logs_table(db_schema, use_row_ids: bool = False):
    """Create db_logs table with optimized sorting keys."""
    
    columns = [
        ('timestamp', pa.timestamp('us')),       # Sorting key 1: Time-series queries
        ('host', pa.string()),                   # Sorting key 2: Per-host filtering
        ('database_name', pa.string()),          # Sorting key 3: Per-database filtering
        ('log_level', pa.string()),              # Sorting key 4: Severity filtering
        ('source', pa.string()),
        ('environment', pa.string()),
        ('event_type', pa.string()),
        ('message', pa.string()),
        ('tags', pa.string()),                   # JSON as string
        ('metadata', pa.string()),               # JSON as string
        ('created_at', pa.timestamp('us')),
        ('id', pa.string()),                     # UUID for deduplication
    ]
    
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))
    
    schema = pa.schema(columns)
    
    table = db_schema.create_table(
        'db_logs',
        schema,
        fail_if_exists=False,
        use_external_row_ids_allocation=use_row_ids,
        sorting_key=['timestamp', 'host', 'database_name', 'log_level']
    )
    
    print(f"✓ Created table: db_logs")
    print(f"  Sorting keys: timestamp, host, database_name, log_level")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def create_queries_table(db_schema, use_row_ids: bool = False):
    """Create db_queries table with optimized sorting keys."""
    
    columns = [
        ('timestamp', pa.timestamp('us')),       # Sorting key 1: Time-series queries
        ('host', pa.string()),                   # Sorting key 2: Per-host filtering
        ('database_name', pa.string()),          # Sorting key 3: Per-database filtering
        ('mean_time_ms', pa.float64()),          # Sorting key 4: Performance filtering (slow queries)
        ('source', pa.string()),
        ('environment', pa.string()),
        ('query_id', pa.string()),
        ('query_text', pa.string()),
        ('query_hash', pa.string()),
        ('calls', pa.int64()),
        ('total_time_ms', pa.float64()),
        ('min_time_ms', pa.float64()),
        ('max_time_ms', pa.float64()),
        ('stddev_time_ms', pa.float64()),
        ('rows_affected', pa.int64()),
        ('cache_hit_ratio', pa.float64()),
        ('tags', pa.string()),                   # JSON as string
        ('metadata', pa.string()),               # JSON as string
        ('created_at', pa.timestamp('us')),
        ('id', pa.string()),                     # UUID for deduplication
    ]
    
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))
    
    schema = pa.schema(columns)
    
    table = db_schema.create_table(
        'db_queries',
        schema,
        fail_if_exists=False,
        use_external_row_ids_allocation=use_row_ids,
        sorting_key=['timestamp', 'host', 'database_name', 'mean_time_ms']
    )
    
    print(f"✓ Created table: db_queries")
    print(f"  Sorting keys: timestamp, host, database_name, mean_time_ms")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create VAST Database tables for observability data'
    )
    parser.add_argument('--host', required=True, help='VAST Database host')
    parser.add_argument('--port', type=int, default=5432, help='VAST Database port')
    parser.add_argument('--database', default='observability', help='Database name')
    parser.add_argument('--schema', default='observability', help='Schema name')
    parser.add_argument('--access-key', required=True, help='VAST access key')
    parser.add_argument('--secret-key', required=True, help='VAST secret key')
    parser.add_argument('--use-row-ids', action='store_true', 
                       help='Use external row ID allocation (user-controlled)')
    parser.add_argument('--recreate', action='store_true',
                       help='Drop existing tables before creating')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("VAST Database - Observability Tables Setup")
    print("=" * 70)
    print()
    
    # Connect to VAST
    print(f"Connecting to VAST Database...")
    print(f"  Host: {args.host}:{args.port}")
    print(f"  Database: {args.database}")
    print(f"  Schema: {args.schema}")
    print()
    
    session = connect(
        endpoint=f"http://{args.host}:{args.port}",
        access=args.access_key,
        secret=args.secret_key
    )
    
    database = session.database(args.database)
    
    # Create schema if it doesn't exist
    try:
        db_schema = database.schema(args.schema)
    except:
        print(f"Creating schema: {args.schema}")
        db_schema = database.create_schema(args.schema)
    
    print(f"✓ Connected to schema: {args.schema}")
    print()
    
    # Drop existing tables if recreate flag is set
    if args.recreate:
        print("Dropping existing tables...")
        for table_name in ['db_metrics', 'db_logs', 'db_queries']:
            try:
                db_schema.drop_table(table_name)
                print(f"  ✓ Dropped: {table_name}")
            except:
                print(f"  - Not found: {table_name}")
        print()
    
    # Create tables
    print("Creating tables...")
    print()
    
    create_metrics_table(db_schema, use_row_ids=args.use_row_ids)
    print()
    
    create_logs_table(db_schema, use_row_ids=args.use_row_ids)
    print()
    
    create_queries_table(db_schema, use_row_ids=args.use_row_ids)
    print()
    
    print("=" * 70)
    print("✓ All tables created successfully!")
    print("=" * 70)
    print()
    print("Query examples:")
    print()
    print("  # Time range query (uses sorting key)")
    print("  SELECT * FROM observability.db_metrics")
    print("  WHERE timestamp BETWEEN '2025-01-01' AND '2025-01-02'")
    print()
    print("  # Host + time query (uses sorting keys)")
    print("  SELECT * FROM observability.db_logs")
    print("  WHERE timestamp > '2025-01-01' AND host = 'prod-db-1'")
    print()
    print("  # Slow queries (uses sorting key on mean_time_ms)")
    print("  SELECT * FROM observability.db_queries")
    print("  WHERE mean_time_ms > 1000")
    print("  ORDER BY mean_time_ms DESC")
    print()
    
    if args.use_row_ids:
        print("  # Row ID range query")
        print("  SELECT * FROM observability.db_metrics")
        print("  WHERE vastdb_rowid > 1000 AND vastdb_rowid < 2000")
        print()


if __name__ == '__main__':
    main()
