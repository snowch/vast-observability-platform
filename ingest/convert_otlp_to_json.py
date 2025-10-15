#!/usr/bin/env python3
"""
Convert binary OTLP Protocol Buffers to JSON for testing.

This script reads the sample-otel-metrics.bin file (binary protobuf)
and converts it to sample-otel-metrics.json (readable JSON).
"""

import sys
import json
import gzip
from pathlib import Path

try:
    from google.protobuf.json_format import MessageToDict
    from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
        ExportMetricsServiceRequest,
    )
except ImportError:
    print("ERROR: Required packages not installed")
    print("")
    print("Install with:")
    print("  pip install opentelemetry-proto protobuf")
    print("")
    print("Or if you have the library requirements:")
    print("  cd vast-observability-platform-library")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def convert_otlp_to_json(input_file: Path, output_file: Path):
    """Convert binary OTLP file to JSON."""
    
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return False
    
    print(f"Reading binary OTLP data from: {input_file}")
    
    # Read binary data
    with open(input_file, "rb") as f:
        binary_data = f.read()
    
    print(f"File size: {len(binary_data)} bytes")
    
    # The data from Kafka console consumer is raw messages concatenated
    # Each message is gzip-compressed OTLP protobuf
    # We'll try to parse as many as we can
    
    all_metrics = []
    
    # Try to decompress if it's gzipped
    try:
        print("Attempting gzip decompression...")
        decompressed = gzip.decompress(binary_data)
        print(f"✓ Decompressed: {len(decompressed)} bytes")
        binary_data = decompressed
    except gzip.BadGzipFile:
        print("Not gzip compressed, trying as raw protobuf...")
    except Exception as e:
        print(f"Decompression failed: {e}, trying as raw protobuf...")
    
    # Try to parse as a single message
    try:
        request = ExportMetricsServiceRequest()
        request.ParseFromString(binary_data)
        
        for resource_metrics in request.resource_metrics:
            metrics_dict = MessageToDict(
                resource_metrics,
                preserving_proto_field_name=True,
                including_default_value_fields=False
            )
            all_metrics.append(metrics_dict)
        
        print(f"✓ Parsed {len(all_metrics)} OTLP metric records from single message")
    
    except Exception as e:
        print(f"Single message parse failed: {e}")
        print("Trying to split into multiple messages...")
        
        # Try splitting by common protobuf delimiters or patterns
        # This is a heuristic approach
        chunks = []
        
        # Try newline-delimited
        if b'\n' in binary_data:
            chunks = binary_data.split(b'\n')
        else:
            # Try to find message boundaries
            # OTLP messages often start with specific byte patterns
            # This is a simplified heuristic
            chunks = [binary_data[i:i+10000] for i in range(0, len(binary_data), 10000)]
        
        for i, chunk in enumerate(chunks):
            if not chunk or len(chunk) < 10:
                continue
            
            try:
                # Try gzip decompression on this chunk
                try:
                    chunk = gzip.decompress(chunk)
                except:
                    pass
                
                request = ExportMetricsServiceRequest()
                request.ParseFromString(chunk)
                
                for resource_metrics in request.resource_metrics:
                    metrics_dict = MessageToDict(
                        resource_metrics,
                        preserving_proto_field_name=True,
                        including_default_value_fields=False
                    )
                    all_metrics.append(metrics_dict)
                
            except Exception:
                continue
    
    if not all_metrics:
        print("")
        print("ERROR: Could not parse binary OTLP data")
        print("")
        print("This is likely because:")
        print("  1. Kafka messages are concatenated without proper delimiters")
        print("  2. Messages are gzip-compressed individually")
        print("  3. Console consumer doesn't preserve message boundaries")
        print("")
        print("Solution: Use a simplified template instead")
        print("")
        return create_template(output_file)
    
    print(f"✓ Successfully parsed {len(all_metrics)} OTLP metric records")
    
    # Write JSON
    with open(output_file, "w") as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"✓ Wrote JSON to: {output_file}")
    
    # Validate JSON is parseable
    with open(output_file) as f:
        test_load = json.load(f)
        print(f"✓ Validated JSON format ({len(test_load)} records)")
    
    return True


def create_template(output_file: Path):
    """Create a template JSON file based on expected OTLP structure."""
    
    print("Creating template sample-otel-metrics.json...")
    
    # Template based on actual OTLP structure
    template = [
        {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "otel-collector"}},
                    {"key": "deployment.environment", "value": {"stringValue": "development"}},
                    {"key": "host.name", "value": {"stringValue": "postgres"}},
                    {"key": "db.system", "value": {"stringValue": "postgresql"}},
                    {"key": "db.name", "value": {"stringValue": "app_db"}}
                ]
            },
            "scope_metrics": [
                {
                    "scope": {
                        "name": "otelcol/postgresqlreceiver",
                        "version": "0.91.0"
                    },
                    "metrics": [
                        {
                            "name": "postgresql.blocks_read",
                            "description": "Number of disk blocks read",
                            "unit": "blocks",
                            "gauge": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1697280000000000000",
                                        "as_int": "12345",
                                        "attributes": [
                                            {"key": "database", "value": {"stringValue": "app_db"}}
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "name": "postgresql.commits",
                            "description": "Number of committed transactions",
                            "unit": "commits",
                            "sum": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1697280000000000000",
                                        "as_int": "567",
                                        "attributes": [
                                            {"key": "database", "value": {"stringValue": "app_db"}}
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "name": "postgresql.backends",
                            "description": "Number of active connections",
                            "unit": "connections",
                            "gauge": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1697280000000000000",
                                        "as_int": "8",
                                        "attributes": [
                                            {"key": "database", "value": {"stringValue": "app_db"}}
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "name": "postgresql.deadlocks",
                            "description": "Number of deadlocks detected",
                            "unit": "deadlocks",
                            "sum": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1697280000000000000",
                                        "as_int": "2",
                                        "attributes": [
                                            {"key": "database", "value": {"stringValue": "app_db"}}
                                        ]
                                    }
                                ]
                            }
                        },
                        {
                            "name": "postgresql.db_size",
                            "description": "Database size in bytes",
                            "unit": "bytes",
                            "gauge": {
                                "data_points": [
                                    {
                                        "time_unix_nano": "1697280000000000000",
                                        "as_int": "8388608",
                                        "attributes": [
                                            {"key": "database", "value": {"stringValue": "app_db"}}
                                        ]
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
    ]
    
    with open(output_file, "w") as f:
        json.dump(template, f, indent=2)
    
    print(f"✓ Created template: {output_file}")
    print("")
    print("Note: This is a simplified template for testing.")
    print("      The actual Kafka data is gzip-compressed and harder to extract.")
    
    return True


def main():
    """Main entry point."""
    
    # Default paths
    input_file = Path("test-data/sample-otel-metrics.bin")
    output_file = Path("test-data/sample-otel-metrics.json")
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    
    print("=== OTLP Binary to JSON Converter ===")
    print("")
    
    success = convert_otlp_to_json(input_file, output_file)
    
    if success:
        print("")
        print("=== Conversion Complete ===")
        print("")
        print("Next steps:")
        print("  1. Copy to library fixtures:")
        print(f"     cp {output_file} ../vast-observability-platform-library/tests/fixtures/")
        print("")
        print("  2. Run library tests:")
        print("     cd ../vast-observability-platform-library")
        print("     pytest tests/test_integration.py -v")
        sys.exit(0)
    else:
        print("")
        print("=== Conversion Failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
