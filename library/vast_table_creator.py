#!/usr/bin/env python3
"""
Create VAST Database tables for observability data using official VAST API.

This version uses the new extensible, entity-centric schema with unified 'events',
'metrics', and 'entities' tables, allowing for easy integration of new data sources.

Usage:
    # Using .env file (recommended):
    python vast_table_creator.py

    # Using command-line arguments (overrides .env):
    python vast_table_creator.py --endpoint http://vast.example.com:5432 \
                                  --bucket observability --schema observability \
                                  --access-key YOUR_KEY --secret-key YOUR_SECRET

    # Recreate all tables from scratch:
    python vast_table_creator.py --recreate
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


def create_events_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create the unified 'events' table for logs, queries, and other event types."""
    
    columns = [
        ('timestamp', pa.timestamp('us')),      # Sorting key 1: Time-series queries
        ('entity_id', pa.string()),             # Sorting key 2: Per-entity filtering
        ('event_type', pa.string()),            # Sorting key 3: Event type filtering
        ('source', pa.string()),                # e.g., 'postgresql', 'cisco_ios', 'linux'
        ('environment', pa.string()),
        ('message', pa.string()),               # Human-readable summary
        ('tags', pa.string()),                  # JSON as string for indexed tags
        ('attributes', pa.string()),            # JSON as string for detailed, event-specific payload
        ('trace_id', pa.string()),              # For correlation across events
        ('id', pa.string()),                    # UUID for deduplication
        ('created_at', pa.timestamp('us')),
    ]
    
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))
    
    arrow_schema = pa.schema(columns)
    
    create_kwargs = {
        'fail_if_exists': False,
        'use_external_row_ids_allocation': use_row_ids,
    }
    
    if supports_sorting:
        create_kwargs['sorting_key'] = ['entity_id', 'timestamp', 'event_type']
    
    table = schema.create_table('events', arrow_schema, **create_kwargs)
    
    print(f"✓ Created unified table: events")
    if supports_sorting:
        print(f"  Sorting keys: entity_id, timestamp, event_type")
    
    return table


def create_metrics_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create the 'metrics' table, now linked to entities."""
    
    columns = [
        ('metric_name', pa.string()),           # Sorting key 1: Metric name filtering
        ('entity_id', pa.string()),             # Sorting key 2: Per-entity filtering
        ('timestamp', pa.timestamp('us')),      # Sorting key 3: Time-series queries
        ('source', pa.string()),
        ('environment', pa.string()),
        ('metric_value', pa.float64()),
        ('metric_type', pa.string()),
        ('unit', pa.string()),
        ('tags', pa.string()),                  # JSON as string
        ('metadata', pa.string()),              # JSON as string
        ('created_at', pa.timestamp('us')),
        ('id', pa.string()),
    ]
    
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))
        
    arrow_schema = pa.schema(columns)
    
    create_kwargs = {'fail_if_exists': False}
    if supports_sorting:
        create_kwargs['sorting_key'] = ['metric_name', 'entity_id', 'timestamp']
        
    table = schema.create_table('metrics', arrow_schema, **create_kwargs)
    print(f"✓ Created table: metrics")
    if supports_sorting:
        print(f"  Sorting keys: metric_name, entity_id, timestamp")
        
    return table


def create_entities_table(schema, use_row_ids: bool = False, supports_sorting: bool = False):
    """Create the 'entities' table to store metadata about monitored systems."""
    
    columns = [
        ('entity_id', pa.string()),             # Sorting key 1: Primary key
        ('entity_type', pa.string()),           # Sorting key 2: Type filtering (e.g., 'host', 'database')
        ('first_seen', pa.timestamp('us')),
        ('last_seen', pa.timestamp('us')),
        ('attributes', pa.string()),            # JSON as string for IP, OS version, etc.
    ]
    
    if use_row_ids:
        columns.insert(0, ('vastdb_rowid', pa.int64()))

    arrow_schema = pa.schema(columns)
    
    create_kwargs = {'fail_if_exists': False}
    if supports_sorting:
        create_kwargs['sorting_key'] = ['entity_type', 'entity_id']

    table = schema.create_table('entities', arrow_schema, **create_kwargs)
    print(f"✓ Created table: entities")
    if supports_sorting:
        print(f"  Sorting keys: entity_type, entity_id")
        
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
        description='Create VAST Database tables for an extensible observability schema.',
        epilog='Values can be provided via .env file or command-line arguments. '
               'Command-line arguments override .env values.'
    )
    parser.add_argument('--endpoint', default=default_endpoint,
                       help='VAST endpoint URL (e.g., http://vast.example.com:5432)')
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
    
    print("\n" + "=" * 70)
    print("VAST Database - Extensible Observability Schema Setup")
    print("=" * 70 + "\n")
    
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
    vast_version = getattr(session.api, 'vast_version', None)
    version_str = '.'.join(map(str, vast_version)) if vast_version else 'Unknown'
    supports_sorting = supports_sorting_keys(vast_version)
    
    print(f"  VAST Version: {version_str}")
    print(f"  Sorting Keys: {'Supported' if supports_sorting else 'Not supported (requires 5.4+)'}\n")
    
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
            # Include old table names to clean up previous schema versions
            for table_name in ['events', 'metrics', 'entities', 'db_logs', 'db_queries', 'db_metrics']:
                try:
                    db_schema.drop_table(table_name)
                    print(f"  ✓ Dropped: {table_name}")
                except Exception:
                    # Ignore if table doesn't exist
                    pass
            print()
        
        # Create tables
        print("Creating tables with new extensible schema...")
        print()
        
        create_events_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
        
        create_metrics_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
        
        create_entities_table(db_schema, use_row_ids=args.use_row_ids, supports_sorting=supports_sorting)
        print()
    
    print("=" * 70)
    print("✓ All tables created successfully!")
    print("=" * 70 + "\n")
    print("Query examples for the new schema:\n")
    print("  # Find all events for a specific host")
    print(f"  SELECT * FROM {args.schema}.events")
    print("  WHERE entity_id = 'prod-db-1' AND timestamp > '2025-01-01'\n")
    print("  # Find all slow MongoDB queries")
    print(f"  SELECT * FROM {args.schema}.events")
    print("  WHERE event_type = 'mongo_slow_query' AND source = 'mongodb'\n")
    print("  # Get CPU usage for a specific host")
    print(f"  SELECT * FROM {args.schema}.metrics")
    print("  WHERE metric_name = 'system.cpu.utilization' AND entity_id = 'web-server-5'\n")

if __name__ == '__main__':
    main()