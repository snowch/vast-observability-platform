# Project Scope: Database Observability Collection Layer

This document clearly defines what this project **does** and **does not** do.

---

## ✅ What This Project DOES

### 1. Data Collection
- ✅ Connects to PostgreSQL databases (agentless, read-only)
- ✅ Collects metrics via OpenTelemetry Collector
- ✅ Collects logs via custom Python collector
- ✅ Collects query analytics via pg_stat_statements
- ✅ Generates test database load for development

### 2. Data Publishing
- ✅ Publishes **raw, unprocessed** data to Kafka
- ✅ Three topics: `otel-metrics`, `raw-logs`, `raw-queries`
- ✅ OTLP format for metrics (binary protobuf)
- ✅ JSON format for logs and queries

### 3. Infrastructure
- ✅ PostgreSQL database with monitoring user
- ✅ Single Kafka instance (`kafka-ingestion`)
- ✅ OpenTelemetry Collector container
- ✅ Python Collector container
- ✅ Load Simulator container
- ✅ Kafka UI for topic monitoring

### 4. Development Tools
- ✅ Docker Compose setup
- ✅ Makefile with useful commands
- ✅ Health checks
- ✅ Debugging tools
- ✅ Local development environment

---

## ❌ What This Project DOES NOT Do

### 1. Data Processing
- ❌ No data normalization
- ❌ No data enrichment
- ❌ No data aggregation
- ❌ No data transformation
- ❌ No schema evolution

### 2. Data Storage
- ❌ No VAST Database integration
- ❌ No long-term storage
- ❌ No data warehouse
- ❌ No time-series database
- ❌ Data only retained in Kafka (7-90 days)

### 3. Data Consumption
- ❌ No output Kafka topics
- ❌ No processed data streams
- ❌ No alert generation
- ❌ No downstream processors
- ❌ No event-driven actions

### 4. Visualization & Analytics
- ❌ No dashboards
- ❌ No Apache Superset
- ❌ No Trino/Presto query engine
- ❌ No BI tools integration
- ❌ No reports

### 5. Advanced Features
- ❌ No MongoDB support (code exists but not deployed)
- ❌ No Redis support (code exists but not deployed)
- ❌ No Bytewax streaming processor
- ❌ No VAST Functions integration
- ❌ No AI/ML analytics
- ❌ No anomaly detection
- ❌ No correlation engine

### 6. Production Features
- ❌ No authentication/authorization
- ❌ No TLS/SSL encryption
- ❌ No multi-tenancy
- ❌ No high availability
- ❌ No disaster recovery
- ❌ No observability of the observability system

---

## 🔄 What Belongs in the Processor Project

The separate **`vastdb-processor`** project should implement:

### Data Processing Pipeline
```
[Kafka Ingestion Topics]
       ↓
   [Bytewax Streaming / VAST Functions]
       ↓
   [vastdb-observability Python Library]
       ├── Normalizer (common schema)
       ├── Enricher (add metadata)
       ├── Aggregator (time-series rollups)
       └── Validator (data quality)
       ↓
[Kafka Output Topics]
       ├── processed-metrics
       ├── processed-logs
       ├── processed-queries
       └── alerts
       ↓
   [VAST Database]
       ├── db_metrics table
       ├── db_logs table
       └── db_queries table
       ↓
   [Analytics Layer]
       ├── Trino (SQL queries)
       ├── Superset (dashboards)
       └── AI Agents (insights)
```

### Components Needed in Processor
1. **vastdb-observability Python library**
   - `collectors/` (from ingestion topics, not databases)
   - `processors/` (normalize, enrich, aggregate)
   - `exporters/` (to output Kafka, VAST DB)

2. **Bytewax dataflow** or **VAST Functions**
   - Streaming data processor
   - Stateful aggregations
   - Windowing operations

3. **Output Kafka instance** (`kafka-output`)
   - Separate from ingestion Kafka
   - Clean separation of concerns
   - Processed data only

4. **VAST Database**
   - Time-series optimized storage
   - SQL interface via Trino
   - Long-term retention (years)

5. **Analytics Layer**
   - Trino query engine
   - Apache Superset dashboards
   - Pre-built observability dashboards

6. **Alerting System**
   - Rule engine
   - Alert aggregation
   - Notification channels

---

## 📊 Data Flow Architecture

### Current Project (Collection)
```
[Databases] → [Collectors] → [kafka-ingestion] → (end here)
                                  ↓
                           [Kafka UI for monitoring]
```

### Complete System (with Processor)
```
[Databases] → [Collectors] → [kafka-ingestion] 
                                  ↓
                           [Processor Service]
                                  ↓
                           [kafka-output]
                                  ↓
                           [VAST Database]
                                  ↓
                           [Analytics/Dashboards]
```

---

## 🎯 Project Boundaries Summary

| Capability | This Project | Processor Project |
|------------|--------------|-------------------|
| Database connection | ✅ Yes | ❌ No |
| Metrics collection | ✅ Yes | ❌ No |
| Raw data publishing | ✅ Yes | ❌ No |
| Data processing | ❌ No | ✅ Yes |
| Data enrichment | ❌ No | ✅ Yes |
| Data storage | ❌ No | ✅ Yes |
| Visualization | ❌ No | ✅ Yes |
| Alerting | ❌ No | ✅ Yes |

---

## 🚀 Integration Points

### How This Project Connects to Processor

**Topic Interface:**
- This project **produces** to: `otel-metrics`, `raw-logs`, `raw-queries`
- Processor project **consumes** from: same topics
- Clean decoupling via Kafka

**No Direct Integration:**
- No shared databases
- No shared code (initially)
- No RPC calls
- Independent deployment
- Independent scaling

**Shared Library (Future):**
- `vastdb-observability` Python library
- Common data models
- Shared utilities
- But each project uses different modules

---

## 📁 Repository Structure Recommendation

### Option 1: Monorepo
```
db-observability/
├── collection/          # This project
│   ├── docker-compose.yml
│   ├── otel-collector/
│   ├── python-collector/
│   └── load-simulator/
├── processor/           # Processor project
│   ├── docker-compose.yml
│   ├── bytewax-processor/
│   └── vast-functions/
├── shared/
│   └── vastdb-observability/  # Shared Python library
└── docs/
```

### Option 2: Separate Repos (Current)
```
db-observability-collection/    # This repo
└── (everything in this project)

vastdb-processor/              # Separate repo
└── (processor implementation)

vastdb-observability/          # Shared library repo
└── (Python library package)
```

---

## 🔧 Development Workflow

### Working on Collection Layer Only
```bash
cd db-observability-collection/
make up
make kafka-consume-queries  # See raw data
```

### Working on Processor
```bash
# Terminal 1: Start collection layer
cd db-observability-collection/
make up

# Terminal 2: Start processor
cd vastdb-processor/
make up

# Data flows: Collection → kafka-ingestion → Processor → kafka-output → VAST DB
```

### Testing Integration
```bash
# Check data flow
make kafka-topics  # Should see all topics

# Consume from ingestion
make kafka-consume-queries

# Consume from output (in processor project)
make kafka-consume-processed
```

---

## 🎓 Understanding the Design

### Why Separate Projects?

1. **Separation of Concerns**
   - Collection: Get data from sources
   - Processing: Transform data
   - Clear responsibilities

2. **Independent Scaling**
   - Scale collectors based on # of databases
   - Scale processors based on data volume
   - Different resource requirements

3. **Development Velocity**
   - Teams can work independently
   - Faster iteration cycles
   - Smaller, focused codebases

4. **Deployment Flexibility**
   - Deploy collection close to databases
   - Deploy processor in central location
   - Different update cadences

5. **Technology Flexibility**
   - Collection uses OTel + Python
   - Processor can use Bytewax/Spark/Flink
   - Change one without affecting the other

---

## 📝 Next Steps

1. **Complete this project:**
   - ✅ Fix remaining bugs
   - ✅ Add documentation
   - ✅ Test with multiple databases
   - ✅ Production hardening

2. **Start processor project:**
   - Create new repository/folder
   - Implement vastdb-observability library
   - Build Bytewax processor
   - Integrate VAST Database
   - Create dashboards

3. **Integration testing:**
   - Run both projects together
   - Verify end-to-end data flow
   - Performance testing
   - Failure scenarios

---

## ⚠️ Common Misconceptions

### ❌ Wrong: "This is the complete observability platform"
**✅ Correct:** This is only the collection layer. Processor is needed for storage and analytics.

### ❌ Wrong: "Data in Kafka is processed and enriched"
**✅ Correct:** Data in Kafka is raw and unprocessed. Processing happens in separate project.

### ❌ Wrong: "I can query historical data from this project"
**✅ Correct:** Only Kafka retention (7-90 days). VAST Database in processor project for historical queries.

### ❌ Wrong: "Dashboards and alerts are included"
**✅ Correct:** No visualization or alerting. That's in the processor project with Superset.

### ❌ Wrong: "kafka-output should be in this project"
**✅ Correct:** Only kafka-ingestion is needed here. kafka-output belongs in processor project.

---

## 🎯 Success Criteria

### For This Project
- ✅ Collectors run reliably
- ✅ Data flows to Kafka topics
- ✅ Topics contain expected data formats
- ✅ Health checks pass
- ✅ Documentation is complete

### For Complete System (Collection + Processor)
- ✅ Data stored in VAST Database
- ✅ Dashboards show insights
- ✅ Alerts fire on anomalies
- ✅ Query performance is good
- ✅ System scales to 100+ databases

---

This document serves as the contract between the collection and processor projects. Any changes to topic schemas or data formats should be coordinated between teams.