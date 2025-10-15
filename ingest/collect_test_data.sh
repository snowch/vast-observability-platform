#!/bin/bash
# collect_test_data.sh
# Collects sample data from Kafka topics for library testing

set -e

# Auto-detect docker compose command (v1: "docker-compose", v2: "docker compose")
if [ -n "$DOCKER_COMPOSE" ]; then
    # Use environment variable if set (already set by Makefile)
    DC="$DOCKER_COMPOSE"
    echo "=== Collecting Test Data from Kafka ==="
    echo "Using: $DC (from DOCKER_COMPOSE env var)"
    echo ""
else
    # Auto-detect: try docker-compose first (v1), then docker compose (v2)
    echo "=== Collecting Test Data from Kafka ==="
    if command -v docker-compose >/dev/null 2>&1; then
        DC="docker-compose"
        echo "Using: $DC (auto-detected v1)"
    elif docker compose version >/dev/null 2>&1; then
        DC="docker compose"
        echo "Using: $DC (auto-detected v2)"
    else
        echo "❌ Neither 'docker-compose' nor 'docker compose' found"
        echo "   Please install Docker Compose"
        exit 1
    fi
    echo ""
fi

# Ensure services are running
echo "Checking if Kafka is running..."
if ! $DC ps 2>/dev/null | grep -q "kafka-ingestion"; then
    echo "❌ Kafka not running. Start services first: make up"
    exit 1
fi

if ! $DC ps 2>/dev/null | grep "kafka-ingestion" | grep -q "Up"; then
    echo "❌ Kafka container exists but is not Up. Try: make restart"
    exit 1
fi

echo "✓ Kafka is running"
echo ""

# Create output directory
mkdir -p test-data
cd test-data

echo "Collecting samples from each topic..."
echo ""

# 1. Collect raw-logs
echo "📋 Collecting raw-logs..."
$DC exec -T kafka-ingestion kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic raw-logs \
    --from-beginning \
    --max-messages 10 \
    --timeout-ms 10000 2>/dev/null \
    > sample-raw-logs.json || echo "Warning: Could not collect raw-logs"

if [ -s sample-raw-logs.json ]; then
    LOGS_COUNT=$(wc -l < sample-raw-logs.json)
    echo "  ✓ Collected $LOGS_COUNT log samples"
    echo "  ℹ Note: File is JSON Lines format (one JSON per line)"
else
    echo "  ⚠ No log samples found (topic may be empty)"
fi

# 2. Collect raw-queries
echo "📊 Collecting raw-queries..."
$DC exec -T kafka-ingestion kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic raw-queries \
    --from-beginning \
    --max-messages 10 \
    --timeout-ms 10000 2>/dev/null \
    > sample-raw-queries.json || echo "Warning: Could not collect raw-queries"

if [ -s sample-raw-queries.json ]; then
    QUERIES_COUNT=$(wc -l < sample-raw-queries.json)
    echo "  ✓ Collected $QUERIES_COUNT query samples"
    echo "  ℹ Note: File is JSON Lines format (one JSON per line)"
else
    echo "  ⚠ No query samples found (topic may be empty)"
fi

# 3. Collect otel-metrics (binary Protocol Buffers)
echo "📈 Collecting otel-metrics..."
$DC exec -T kafka-ingestion kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic otel-metrics \
    --from-beginning \
    --max-messages 5 \
    --timeout-ms 10000 2>/dev/null \
    > sample-otel-metrics.bin || echo "Warning: Could not collect otel-metrics"

if [ -s sample-otel-metrics.bin ]; then
    METRICS_SIZE=$(wc -c < sample-otel-metrics.bin)
    echo "  ✓ Collected binary OTLP data (${METRICS_SIZE} bytes)"
    echo "  ℹ Note: This is binary Protocol Buffers - cannot be used directly in tests"
    echo "  ℹ Use the manually created sample-otel-metrics.json instead"
else
    echo "  ⚠ No metric samples found (topic may be empty)"
fi

echo ""
echo "=== Collection Complete ==="
echo ""

# Validate JSON structure
echo "Validating JSON structure..."
python3 - <<EOF
import json
import sys

def validate_jsonl(filename):
    try:
        with open(filename) as f:
            lines = [line for line in f if line.strip()]
            if not lines:
                return 0, "Empty file"
            
            for i, line in enumerate(lines, 1):
                try:
                    data = json.loads(line)
                    required = ["timestamp", "source", "data_type", "host", "database"]
                    missing = [k for k in required if k not in data]
                    if missing:
                        return 0, f"Line {i} missing fields: {missing}"
                except json.JSONDecodeError as e:
                    return 0, f"Line {i} invalid JSON: {e}"
            
            return len(lines), "Valid"
    except FileNotFoundError:
        return 0, "File not found"

# Validate logs
logs_count, logs_status = validate_jsonl("sample-raw-logs.json")
print(f"  raw-logs: {logs_count} samples - {logs_status}")

# Validate queries
queries_count, queries_status = validate_jsonl("sample-raw-queries.json")
print(f"  raw-queries: {queries_count} samples - {queries_status}")

if logs_count == 0 and queries_count == 0:
    print("\n⚠ Warning: No valid samples collected!")
    print("   Make sure load simulator is running and generating traffic.")
    sys.exit(1)
EOF

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Copy JSON files to library test fixtures:"
echo "   cp test-data/sample-raw-*.json ../vastdb-observability/tests/fixtures/"
echo ""
echo "2. Manually create sample-otel-metrics.json for testing:"
echo "   # The .bin file is binary Protocol Buffers and can't be used directly"
echo "   # Use the provided sample-otel-metrics.json template instead"
echo "   # Or copy from: vastdb-observability/tests/fixtures/sample-otel-metrics.json"
echo ""
echo "3. Run library tests:"
echo "   cd ../vastdb-observability"
echo "   pytest tests/test_integration.py -v"
echo ""
