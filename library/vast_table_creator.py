#!/usr/bin/env python3
"""
Create VAST Database tables for observability data using official VAST API.

Usage:
    # Using .env file (recommended):
    python vast_table_creator.py

    # Using command-line arguments (overrides .env):
    python vast_table_creator.py --endpoint http://vast.example.com:5432 \
                                  --bucket observability --schema observability \
                                  --access-key YOUR_KEY --secret-key YOUR_SECRET

    # With HTTPS:
    python vast_table_creator.py --endpoint https://vast.example.com \
                                  --bucket observability --schema observability \
                                  --access-key YOUR_KEY --secret-key YOUR_SECRET
"""

import argparse
import pyarrow as pa
import vastdb
import os
from pathlib import Path
from dotenv import load_dotenv


def supports_sorting_keys(vast_version):
    """Check if VAST version supports sorting keys (5.4+)."""
    if vast_version is None or len(vast_version) < 2:
        return False
    major, minor = vast_version[0], vast_version[1]
    return (major, minor) >= (5, 4)


def create_metrics_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create db_metrics table with optimized sorting keys (if supported)."""
    
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
    
    arrow_schema = pa.schema(columns)
    
    # Create table with sorting keys if supported
    create_kwargs = {
        'fail_if_exists': False,
        'use_external_row_ids_allocation': use_row_ids,
    }
    
    if supports_sorting:
        create_kwargs['sorting_key'] = ['timestamp', 'host', 'database_name', 'metric_name']
    
    table = schema.create_table('db_metrics', arrow_schema, **create_kwargs)
    
    print(f"✓ Created table: db_metrics")
    if supports_sorting:
        print(f"  Sorting keys: timestamp, host, database_name, metric_name")
    else:
        print(f"  Sorting keys: Not supported (VAST version < 5.4)")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def create_logs_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create db_logs table with optimized sorting keys (if supported)."""
    
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
    
    arrow_schema = pa.schema(columns)
    
    create_kwargs = {
        'fail_if_exists': False,
        'use_external_row_ids_allocation': use_row_ids,
    }
    
    if supports_sorting:
        create_kwargs['sorting_key'] = ['timestamp', 'host', 'database_name', 'log_level']
    
    table = schema.create_table('db_logs', arrow_schema, **create_kwargs)
    
    print(f"✓ Created table: db_logs")
    if supports_sorting:
        print(f"  Sorting keys: timestamp, host, database_name, log_level")
    else:
        print(f"  Sorting keys: Not supported (VAST version < 5.4)")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def create_queries_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create db_queries table with optimized sorting keys (if supported)."""
    
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
    
    arrow_schema = pa.schema(columns)
    
    create_kwargs = {
        'fail_if_exists': False,
        'use_external_row_ids_allocation': use_row_ids,
    }
    
    if supports_sorting:
        create_kwargs['sorting_key'] = ['timestamp', 'host', 'database_name', 'mean_time_ms']
    
    table = schema.create_table('db_queries', arrow_schema, **create_kwargs)
    
    print(f"✓ Created table: db_queries")
    if supports_sorting:
        print(f"  Sorting keys: timestamp, host, database_name, mean_time_ms")
    else:
        print(f"  Sorting keys: Not supported (VAST version < 5.4)")
    print(f"  Row IDs: {'External (user-controlled)' if use_row_ids else 'Internal (auto-allocated)'}")
    
    return table


def main():
    """Main entry point."""
    # Load .env file if it exists
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded configuration from .env file")
    else:
        print(f"ℹ No .env file found, using command-line arguments only")
    
    # Get defaults from environment variables
    default_endpoint = os.getenv('VAST_ENDPOINT')
    default_bucket = os.getenv('VAST_BUCKET', 'observability')
    default_schema = os.getenv('VAST_SCHEMA', 'observability')
    default_access_key = os.getenv('VAST_ACCESS_KEY')
    default_secret_key = os.getenv('VAST_SECRET_KEY')
    
    parser = argparse.ArgumentParser(
        description='Create VAST Database tables for observability data',
        epilog='Values can be provided via .env file or command-line arguments. '
               'Command-line arguments override .env values.'
    )
    parser.add_argument('--endpoint', default=default_endpoint,
                       help='VAST endpoint URL (e.g., http://vast.example.com:5432 or https://vast.example.com)')
    parser.add_argument('--bucket', default=default_bucket,
                       help='Bucket name (default: %(default)s)')
    parser.add_argument('--schema', default=default_schema,
                       help='Schema name (default: %(default)s)')
    parser.add_argument('--access-key', default=default_access_key,
                       help='VAST access key')
    parser.add_argument('--secret-key', default=default_secret_key,
                       help='VAST secret key')
    parser.add_argument('--use-row-ids', action='store_true', 
                       help='Use external row ID allocation (user-controlled)')
    parser.add_argument('--recreate', action='store_true',
                       help='Drop existing tables before creating')
    
    args = parser.parse_args()
    
    # Validate required parameters
    missing = []
    if not args.endpoint:
        missing.append('--endpoint (or VAST_ENDPOINT in .env)')
    if not args.access_key:
        missing.append('--access-key (or VAST_ACCESS_KEY in .env)')
    if not args.secret_key:
        missing.append('--secret-key (or VAST_SECRET_KEY in .env)')
    
    if missing:
        parser.error(f"Missing required parameters: {', '.join(missing)}")
    
    print()
    print("=" * 70)
    print("VAST Database - Observability Tables Setup")
    print("=" * 70)
    print()
    
    # Connect to VAST using official API
    print(f"Connecting to VAST Database...")
    print(f"  Endpoint: {args.endpoint}")
    print(f"  Bucket: {args.bucket}")
    print(f"  Schema: {args.schema}")
    
    session = vastdb.connect(
        endpoint=args.endpoint,
        access=args.access_key,
        secret=args.secret_key
    )
    
    # Check VAST version for sorting key support
    vast_version = session.api.vast_version
    version_str = '.'.join(map(str, vast_version)) if vast_version else 'Unknown'
    supports_sorting = supports_sorting_keys(vast_version)
    
    print(f"  VAST Version: {version_str}")
    print(f"  Sorting Keys: {'Supported' if supports_sorting else 'Not supported (requires 5.4+)'}")
    print()
    
    # Use transaction to access bucket and schema
    with session.transaction() as tx:
        bucket = tx.bucket(args.bucket)
        
        # Create schema if it doesn't exist, or get existing one
        try:
            db_schema = bucket.schema(args.schema)
            print(f"✓ Using existing schema: {args.schema}")
        except:
            db_schema = bucket.create_schema(args.schema)
            print(f"✓ Created new schema: {args.schema}")
        
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
        
        create_metrics_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
        
        create_logs_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
        
        create_queries_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
    
    # Transaction auto-commits when exiting context
    print("=" * 70)
    print("✓ All tables created successfully!")
    print("=" * 70)
    print()
    print("Query examples:")
    print()
    print("  # Time range query (uses sorting key if available)")
    print(f"  SELECT * FROM {args.schema}.db_metrics")
    print("  WHERE timestamp BETWEEN '2025-01-01' AND '2025-01-02'")
    print()
    print("  # Host + time query (uses sorting keys if available)")
    print(f"  SELECT * FROM {args.schema}.db_logs")
    print("  WHERE timestamp > '2025-01-01' AND host = 'prod-db-1'")
    print()
    print("  # Slow queries (uses sorting key on mean_time_ms if available)")
    print(f"  SELECT * FROM {args.schema}.db_queries")
    print("  WHERE mean_time_ms > 1000")
    print("  ORDER BY mean_time_ms DESC")
    print()
    
    if args.use_row_ids:
        print("  # Row ID range query")
        print(f"  SELECT * FROM {args.schema}.db_metrics")
        print("  WHERE vastdb_rowid > 1000 AND vastdb_rowid < 2000")
        print()


if __name__ == '__main__':
    main()