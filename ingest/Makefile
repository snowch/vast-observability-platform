.PHONY: help build up down restart logs ps clean health debug

# Auto-detect docker compose command
# Prefer docker-compose (v1) if available, otherwise use docker compose (v2)
DOCKER_COMPOSE := $(shell which docker-compose >/dev/null 2>&1 && echo "docker-compose" || echo "docker compose")

help:
	@echo "Database Observability Platform - Available Commands:"
	@echo ""
	@echo "  Using: $(DOCKER_COMPOSE)"
	@echo ""
	@echo "Service Management:"
	@echo "  make build            - Build all Docker images"
	@echo "  make up               - Start all services"
	@echo "  make down             - Stop all services"
	@echo "  make restart          - Restart all services"
	@echo "  make logs             - View logs from all services"
	@echo "  make ps               - Show running services"
	@echo "  make clean            - Stop services and remove volumes"
	@echo "  make health           - Check health of all services"
	@echo "  make debug            - Debug failing services"
	@echo ""
	@echo "Kafka Operations:"
	@echo "  make kafka-topics         - List Kafka topics"
	@echo "  make kafka-consume-metrics - View otel-metrics topic"
	@echo "  make kafka-consume-logs    - View raw-logs topic"
	@echo "  make kafka-consume-queries - View raw-queries topic"
	@echo "  make kafka-ui              - Open Kafka UI in browser"
	@echo ""
	@echo "Database Operations:"
	@echo "  make shell-pg         - Open PostgreSQL shell"
	@echo "  make check-pg-stats   - Check pg_stat_statements"
	@echo ""
	@echo "Collector Operations:"
	@echo "  make logs-otel        - View OTel Collector logs"
	@echo "  make logs-python      - View Python Collector logs"
	@echo "  make logs-simulator   - View Load Simulator logs"
	@echo ""
	@echo "Test Data Collection:"
	@echo "  make collect-test-data         - Collect samples from Kafka topics"
	@echo "  make convert-otlp-to-json      - Convert binary OTLP to JSON"
	@echo "  make validate-test-data        - Validate collected test data"
	@echo "  make copy-test-data-to-library - Copy to library fixtures directory"
	@echo "  make setup-library-tests       - Complete workflow (collect + convert + validate)"
	@echo ""
	@echo "Quick Fixes:"
	@echo "  make fix-permissions  - Fix file permissions"
	@echo "  make rebuild-collectors - Rebuild collector images"
	@echo "  make fix-and-restart  - Apply all fixes and restart"
	@echo ""
	@echo "Override docker command:"
	@echo "  make DOCKER_COMPOSE=docker-compose <target>"
	@echo ""

build:
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) build

up:
	@echo "Starting services..."
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "Waiting for services to start (this takes ~30-60s for Kafka)..."
	@sleep 15
	@echo ""
	@echo "✓ Services started!"
	@echo ""
	@echo "  Kafka UI: http://localhost:8080"
	@echo "  OTel Health: http://localhost:13133/health"
	@echo "  PostgreSQL: localhost:5432"
	@echo ""
	@echo "Next steps:"
	@echo "  make health          # Check all services"
	@echo "  make kafka-topics    # View Kafka topics"
	@echo "  make kafka-ui        # Open Kafka UI"
	@echo ""

down:
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) down

restart: down up

logs:
	$(DOCKER_COMPOSE) logs -f

ps:
	@$(DOCKER_COMPOSE) ps

clean:
	@echo "Stopping services and removing volumes..."
	$(DOCKER_COMPOSE) down -v
	@echo "✓ Cleaned up"

health:
	@echo "=== Service Health Check ==="
	@echo ""
	@echo "PostgreSQL:"
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U app_user -d app_db > /dev/null 2>&1 && echo "  ✓ Healthy" || echo "  ❌ Not ready"
	@echo ""
	@echo "Kafka Ingestion:"
	@$(DOCKER_COMPOSE) exec -T kafka-ingestion kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1 && echo "  ✓ Healthy" || echo "  ❌ Not responding"
	@echo ""
	@echo "OTel Collector:"
	@curl -s http://localhost:13133/health > /dev/null 2>&1 && echo "  ✓ Healthy" || echo "  ❌ Not responding"
	@echo ""
	@echo "Python Collector:"
	@$(DOCKER_COMPOSE) ps | grep python-collector | grep -q "Up" && echo "  ✓ Running" || echo "  ❌ Not running"
	@echo ""
	@echo "Load Simulator:"
	@$(DOCKER_COMPOSE) ps | grep load-simulator | grep -q "Up" && echo "  ✓ Running (generating traffic)" || echo "  ❌ Not running"
	@echo ""

debug:
	@echo "=== Debugging Services ==="
	@echo ""
	@echo "=== All Container Status ==="
	$(DOCKER_COMPOSE) ps -a
	@echo ""
	@echo "=== OTel Collector Logs (last 50 lines) ==="
	$(DOCKER_COMPOSE) logs --tail=50 otel-collector || echo "OTel Collector not found"
	@echo ""
	@echo "=== Python Collector Logs (last 50 lines) ==="
	$(DOCKER_COMPOSE) logs --tail=50 python-collector || echo "Python Collector not found"
	@echo ""
	@echo "=== Load Simulator Logs (last 50 lines) ==="
	$(DOCKER_COMPOSE) logs --tail=50 load-simulator || echo "Load Simulator not found"
	@echo ""
	@echo "=== Kafka Topics ==="
	$(DOCKER_COMPOSE) exec -T kafka-ingestion kafka-topics --bootstrap-server localhost:9092 --list || echo "Kafka not responding"

shell-pg:
	@echo "Opening PostgreSQL shell..."
	$(DOCKER_COMPOSE) exec postgres psql -U app_user -d app_db

shell-python:
	@echo "Opening Python collector shell..."
	$(DOCKER_COMPOSE) exec python-collector bash

simulator-logs:
	@echo "Load Simulator Stats:"
	$(DOCKER_COMPOSE) logs -f load-simulator

stop-simulator:
	@echo "Stopping load simulator..."
	$(DOCKER_COMPOSE) stop load-simulator
	@echo "Load simulator stopped. Database traffic will cease."

start-simulator:
	@echo "Starting load simulator..."
	$(DOCKER_COMPOSE) start load-simulator
	@echo "Load simulator started. Generating database traffic."

kafka-ui:
	@which open > /dev/null && open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Open http://localhost:8080"

logs-otel:
	$(DOCKER_COMPOSE) logs -f otel-collector

logs-python:
	$(DOCKER_COMPOSE) logs -f python-collector

logs-simulator:
	$(DOCKER_COMPOSE) logs -f load-simulator

logs-postgres:
	$(DOCKER_COMPOSE) logs -f postgres

logs-kafka:
	$(DOCKER_COMPOSE) logs -f kafka-ingestion

kafka-topics:
	@echo "=== Kafka Topics (Ingestion Layer) ==="
	@$(DOCKER_COMPOSE) exec -T kafka-ingestion kafka-topics --bootstrap-server localhost:9092 --list || echo "❌ Kafka not ready"
	@echo ""
	@echo "Expected topics:"
	@echo "  - otel-metrics  (OTLP format from OTel Collector)"
	@echo "  - raw-logs      (JSON format from Python Collector)"
	@echo "  - raw-queries   (JSON format from Python Collector)"

kafka-consume-metrics:
	@echo "Consuming messages from otel-metrics topic (Ctrl+C to stop)..."
	@echo "Note: Data is in OTLP (Protocol Buffers) format"
	@echo ""
	$(DOCKER_COMPOSE) exec kafka-ingestion kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic otel-metrics \
		--from-beginning \
		--max-messages 10

kafka-consume-logs:
	@echo "Consuming messages from raw-logs topic (Ctrl+C to stop)..."
	@echo "Note: Data is in JSON format"
	@echo ""
	$(DOCKER_COMPOSE) exec kafka-ingestion kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic raw-logs \
		--from-beginning \
		--max-messages 10

kafka-consume-queries:
	@echo "Consuming messages from raw-queries topic (Ctrl+C to stop)..."
	@echo "Note: Data is in JSON format"
	@echo ""
	$(DOCKER_COMPOSE) exec kafka-ingestion kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic raw-queries \
		--from-beginning \
		--max-messages 10

check-pg-stats:
	@echo "Checking pg_stat_statements..."
	$(DOCKER_COMPOSE) exec -T postgres psql -U app_user -d app_db -c "\
		SELECT COUNT(*) as total_queries FROM pg_stat_statements;"

monitor:
	@echo "Monitoring all logs (Ctrl+C to stop)..."
	$(DOCKER_COMPOSE) logs -f --tail=100

scale-collectors:
	@read -p "How many Python collectors? " count; \
	echo "Scaling to $$count collectors..."; \
	$(DOCKER_COMPOSE) up -d --scale python-collector=$$count

dev: build up logs

prod:
	@echo "Starting in production mode..."
	$(DOCKER_COMPOSE) -f docker-compose.yml up -d
	@make health

# Quick fixes for common issues
fix-permissions:
	@echo "Fixing file permissions..."
	chmod 644 otel-collector-config.yaml
	chmod 644 docker-compose.yml
	@echo "✓ Permissions fixed"

rebuild-collectors:
	@echo "Rebuilding collector images from scratch..."
	$(DOCKER_COMPOSE) build --no-cache python-collector load-simulator
	@echo "✓ Collectors rebuilt"

fix-and-restart:
	@echo "Applying fixes and restarting..."
	@make fix-permissions
	@make rebuild-collectors
	@make restart
	@echo ""
	@echo "Services restarted. Checking status in 15 seconds..."
	@sleep 15
	@make health
	@echo ""
	@echo "View topics: make kafka-topics"
	@echo "View data: make kafka-consume-queries"

# Test Data Collection
collect-test-data:
	@echo "Collecting test data from Kafka topics..."
	@mkdir -p test-data
	@chmod +x collect_test_data.sh
	@DOCKER_COMPOSE='$(DOCKER_COMPOSE)' ./collect_test_data.sh

convert-otlp-to-json:
	@echo "Converting binary OTLP data to JSON..."
	@python3 convert_otlp_to_json.py

validate-test-data:
	@echo "Validating collected test data..."
	@python3 - <<'EOF'
	import json
	from pathlib import Path
	
	test_data = Path("test-data")
	if not test_data.exists():
	    print("❌ test-data directory not found. Run: make collect-test-data")
	    exit(1)
	
	def validate_jsonl(filename):
	    filepath = test_data / filename
	    if not filepath.exists():
	        return 0, "File not found"
	    
	    try:
	        with open(filepath) as f:
	            lines = [line for line in f if line.strip()]
	            if not lines:
	                return 0, "Empty file"
	            
	            for i, line in enumerate(lines, 1):
	                try:
	                    data = json.loads(line)
	                    required = ["timestamp", "source", "data_type", "host", "database"]
	                    missing = [k for k in required if k not in data]
	                    if missing:
	                        return 0, f"Line {i} missing: {missing}"
	                except json.JSONDecodeError:
	                    return 0, f"Line {i} invalid JSON"
	            
	            return len(lines), "Valid"
	    except Exception as e:
	        return 0, str(e)
	
	logs_count, logs_status = validate_jsonl("sample-raw-logs.json")
	queries_count, queries_status = validate_jsonl("sample-raw-queries.json")
	
	print(f"📋 raw-logs:    {logs_count:3d} samples - {logs_status}")
	print(f"📊 raw-queries: {queries_count:3d} samples - {queries_status}")
	
	if logs_count > 0 and queries_count > 0:
	    print("\n✅ Test data is valid and ready to use")
	else:
	    print("\n⚠️  Some test data is missing or invalid")
	    exit(1)
	EOF

setup-library-tests: collect-test-data convert-otlp-to-json validate-test-data
	@echo ""
	@echo "✅ Test data collection complete!"
	@echo ""
	@echo "Files created in test-data/:"
	@ls -lh test-data/sample-*.json 2>/dev/null || echo "  (no files yet)"
	@echo ""
	@echo "To copy to library project:"
	@echo "  make copy-test-data-to-library"

copy-test-data-to-library:
	@echo "Copying test data to library project..."
	@if [ ! -d "../library/tests/fixtures" ]; then \
	    echo "Creating fixtures directory..."; \
	    mkdir -p ../library/tests/fixtures; \
	fi
	@cp test-data/sample-raw-logs.json ../library/tests/fixtures/
	@cp test-data/sample-raw-queries.json ../library/tests/fixtures/
	@if [ -f test-data/sample-otel-metrics.json ]; then \
	    cp test-data/sample-otel-metrics.json ../library/tests/fixtures/; \
	    echo "✅ Copied all 3 test data files to ../library/tests/fixtures/"; \
	else \
	    echo "⚠️  sample-otel-metrics.json not found. Run: make convert-otlp-to-json"; \
	    echo "✓ Copied 2 test data files (logs and queries)"; \
	fi
