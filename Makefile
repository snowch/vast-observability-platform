.PHONY: help build up down restart logs ps clean health debug \
        test-library format-library lint-library typecheck-library \
        run-query create-tables

# Auto-detect docker compose command
DOCKER_COMPOSE := $(shell which docker-compose >/dev/null 2>&1 && echo "docker-compose" || echo "docker compose")

# === Core Platform Management ===

help:
	@echo "VAST Observability Platform - Available Commands:"
	@echo ""
	@echo "  Using: $(DOCKER_COMPOSE)"
	@echo ""
	@echo "Core Platform:"
	@echo "  make build            - Build all Docker images"
	@echo "  make up               - Start all services (ingest + processor)"
	@echo "  make down             - Stop all services"
	@echo "  make restart          - Restart all services"
	@echo "  make logs             - View logs from ALL services"
	@echo "  make ps               - Show running services"
	@echo "  make clean            - Stop services and remove volumes"
	@echo "  make health           - Check health of core services"
	@echo "  make debug            - Debug failing core services"
	@echo ""
	@echo "Component Specific:"
	@echo "  make logs-processor   - View only the processor logs"
	@echo "  make run-query        - Run the VAST DB query script"
	@echo "  make create-tables    - Create/Update VAST DB tables (requires library install)"
	@echo ""
	@echo "Library Development:"
	@echo "  make test-library     - Run library unit tests"
	@echo "  make format-library   - Format library code with Black"
	@echo "  make lint-library     - Lint library code with Ruff"
	@echo "  make typecheck-library- Check library types with MyPy"
	@echo ""
	@echo "Ingestion Layer Details:"
	@echo "  make kafka-topics         - List Kafka topics"
	@echo "  make kafka-consume-metrics - View otel-metrics topic"
	@echo "  make kafka-consume-logs    - View raw-logs topic"
	@echo "  make kafka-consume-queries - View raw-queries topic"
	@echo "  make kafka-ui              - Open Kafka UI in browser"
	@echo "  make shell-pg         - Open PostgreSQL shell"
	@echo "  make check-pg-stats   - Check pg_stat_statements"
	@echo "  make logs-otel        - View OTel Collector logs"
	@echo "  make logs-python      - View Python Collector logs"
	@echo "  make logs-simulator   - View Load Simulator logs"
	@echo ""
	@echo "Test Data Collection (for library):"
	@echo "  make collect-test-data         - Collect samples from Kafka topics"
	@echo "  make copy-test-data-to-library - Copy to library fixtures directory"
	@echo ""

build:
	@echo "Building all Docker images..."
	$(DOCKER_COMPOSE) build

up:
	@echo "Starting all services (ingest + processor)..."
	@cp -n .env.example .env # Copy .env if it doesn't exist
	$(DOCKER_COMPOSE) up -d
	@echo ""
	@echo "Waiting for services to start (this takes ~30-60s for Kafka)..."
	@sleep 15
	@echo ""
	@echo "✓ Platform started!"
	@echo ""
	@echo "  Kafka UI: http://localhost:8080"
	@echo "  OTel Health: http://localhost:13133/health"
	@echo "  PostgreSQL: localhost:5432"
	@echo ""
	@echo "Next steps:"
	@echo "  make health          # Check all services"
	@echo "  make kafka-topics    # View Kafka topics"
	@echo "  make logs-processor  # See processor status"
	@echo ""

down:
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) down

restart: down up

logs:
	$(DOCKER_COMPOSE) logs -f

logs-processor:
	$(DOCKER_COMPOSE) logs -f processor

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
	@$(DOCKER_COMPOSE) exec -T postgres pg_isready -U ${POSTGRES_USER:-app_user} -d ${POSTGRES_DB:-app_db} > /dev/null 2>&1 && echo "  ✓ Healthy" || echo "  ❌ Not ready"
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
	@echo "Processor:"
	@$(DOCKER_COMPOSE) ps | grep processor | grep -q "Up" && echo "  ✓ Running" || echo "  ❌ Not running"
	@echo ""

debug:
	@echo "=== Debugging Services ==="
	@echo ""
	@echo "=== All Container Status ==="
	$(DOCKER_COMPOSE) ps -a
	@echo ""
	@echo "=== Processor Logs (last 50 lines) ==="
	$(DOCKER_COMPOSE) logs --tail=50 processor || echo "Processor not found"
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

# === Component Specific Targets ===

## Query
run-query:
	@echo "Running VAST DB query script..."
	@cp -n .env.example .env # Ensure .env exists for the script
	@cd query && \
	pip install -r requirements.txt > /dev/null 2>&1 && \
	python querier.py && \
	cd ..

## Library / VAST DB Schema
create-tables:
	@echo "Creating VAST DB tables using library script..."
	@cp -n .env.example .env # Ensure .env exists for the script
	@cd library && \
	pip install -e .[dev] > /dev/null 2>&1 && \
	python vast_table_creator.py && \
	cd ..

# === Library Development Targets ===

test-library:
	@echo "Running library tests..."
	@cd library && \
	pip install -e .[dev] > /dev/null 2>&1 && \
	python -m pytest tests/test_processors.py -v && \
	cd ..

format-library:
	@echo "Formatting library code..."
	@cd library && \
	pip install black > /dev/null 2>&1 && \
	black vastdb_observability/ tests/ examples/ && \
	cd ..

lint-library:
	@echo "Linting library code..."
	@cd library && \
	pip install ruff > /dev/null 2>&1 && \
	ruff check vastdb_observability/ && \
	cd ..

typecheck-library:
	@echo "Type checking library code..."
	@cd library && \
	pip install mypy > /dev/null 2>&1 && \
	mypy vastdb_observability/ && \
	cd ..

# === Ingestion Layer Details (Keep as before) ===

shell-pg:
	@echo "Opening PostgreSQL shell..."
	$(DOCKER_COMPOSE) exec postgres psql -U ${POSTGRES_USER:-app_user} -d ${POSTGRES_DB:-app_db}

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
	@echo "  - otel-metrics"
	@echo "  - raw-logs"
	@echo "  - raw-queries"
	@echo "  - raw-host-logs"

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

kafka-consume-host-logs:
	@echo "Consuming messages from raw-host-logs topic (Ctrl+C to stop)..."
	@echo "Note: Data is in JSON format"
	@echo ""
	$(DOCKER_COMPOSE) exec kafka-ingestion kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic raw-host-logs \
		--from-beginning \
		--max-messages 10

check-pg-stats:
	@echo "Checking pg_stat_statements..."
	$(DOCKER_COMPOSE) exec -T postgres psql -U ${POSTGRES_USER:-app_user} -d ${POSTGRES_DB:-app_db} -c "\
		SELECT COUNT(*) as total_queries FROM pg_stat_statements;"

# Test Data Collection
collect-test-data:
	@echo "Collecting test data from Kafka topics..."
	@cd ingest && DOCKER_COMPOSE='$(DOCKER_COMPOSE)' ./collect_test_data.sh && cd ..

copy-test-data-to-library:
	@echo "Copying test data to library project..."
	@if [ ! -d "library/tests/fixtures" ]; then \
	    echo "Creating fixtures directory..."; \
	    mkdir -p library/tests/fixtures; \
	fi
	@cp ingest/test-data/sample-raw-logs.json library/tests/fixtures/
	@cp ingest/test-data/sample-raw-queries.json library/tests/fixtures/
	@if [ -f ingest/test-data/sample-otel-metrics.json ]; then \
	    cp ingest/test-data/sample-otel-metrics.json library/tests/fixtures/; \
	    echo "✅ Copied all 3 test data files to library/tests/fixtures/"; \
	else \
	    echo "⚠️  sample-otel-metrics.json not found. Run: make collect-test-data first, then manually convert or copy."; \
	    echo "✓ Copied 2 test data files (logs and queries)"; \
	fi