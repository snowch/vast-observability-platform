# Quick Fixes for Common Issues

## Your Current Issues

Based on the debug output, you have:
1. **OTel Collector**: Permission denied reading config file
2. **Python Collector**: Module not found error

## Solution 1: Use the Auto-Fix Command

```bash
# This will fix permissions and rebuild everything
make fix-and-restart

# Wait for services to start
sleep 15

# Check if fixed
make health
```

## Solution 2: Manual Steps

### Fix OTel Collector (Permission Denied)

```bash
# Fix file permissions
chmod 644 otel-collector-config.yaml

# Rebuild and restart
docker compose build --no-cache otel-collector
docker compose up -d otel-collector

# Check logs
make logs-otel
```

### Fix Python Collector (Module Not Found)

```bash
# Verify directory structure
ls -la python-collector/collector/

# Should see:
# - __init__.py
# - main.py
# - config.py
# - models.py
# - postgresql_collector.py
# - kafka_exporter.py

# If files are missing, re-run setup.sh

# Rebuild from scratch
docker compose build --no-cache python-collector

# Restart
docker compose up -d python-collector

# Check logs
make logs-python
```

## Solution 3: Nuclear Option (Fresh Start)

```bash
# Stop everything
make clean

# Remove old images
docker compose down --rmi all

# Rebuild everything
make build

# Start fresh
make up

# Check status
make health
```

## Verify Success

After applying fixes:

```bash
# 1. Check all services
make health

# Expected output:
# ✓ PostgreSQL: Healthy
# ✓ OTel Collector: Healthy  
# ✓ Kafka: Healthy
# ✓ Python Collector: Running
# ✓ Load Simulator: Running

# 2. Check OTel is collecting
curl http://localhost:13133/health

# Expected: {"status":"Server available",...}

# 3. Check data flowing to Kafka
make kafka-topics

# Expected to see:
# - raw-metrics
# - raw-logs
# - raw-queries

# 4. View actual data
make kafka-consume-queries
```

## Common Issues Reference

### Issue: Permission Denied (OTel Config)

**Error:**
```
permission denied: open /etc/otel-collector-config.yaml
```

**Fix:**
```bash
chmod 644 otel-collector-config.yaml
make rebuild-collectors
```

### Issue: Module Not Found (Python Collector)

**Error:**
```
ModuleNotFoundError: No module named 'collector'
```

**Fix:**
```bash
# Verify structure
ls python-collector/collector/__init__.py

# Rebuild
docker compose build --no-cache python-collector
docker compose up -d python-collector
```

### Issue: Container Keeps Restarting

**Debug:**
```bash
# Check why it's restarting
make debug

# View recent logs
docker compose logs --tail=100 python-collector
docker compose logs --tail=100 otel-collector
```

### Issue: Can't Connect to PostgreSQL

**Check:**
```bash
# Is PostgreSQL ready?
docker compose exec postgres pg_isready

# Can monitor user connect?
docker compose exec postgres psql -U monitor_user -d app_db -c "SELECT 1;"
```

### Issue: Kafka Not Ready

**Check:**
```bash
# List topics
docker compose exec kafka-ingestion kafka-topics --bootstrap-server localhost:9092 --list

# If empty, wait longer - Kafka takes 30-60s to start
```

## Prevention

To avoid these issues in the future:

1. **Always use setup.sh** - Don't manually create files
2. **Check permissions** - Run `make fix-permissions` after setup
3. **Build properly** - Use `make build` not `docker compose build` directly
4. **Verify structure** - Setup script now validates directory structure

## Still Having Issues?

```bash
# Full diagnostic
make debug > debug.log

# Check the log file
cat debug.log

# Or get help with specific service
make logs-otel       # OTel Collector
make logs-python     # Python Collector
make logs-simulator  # Load Simulator
make logs-postgres   # PostgreSQL
make logs-kafka      # Kafka
```
