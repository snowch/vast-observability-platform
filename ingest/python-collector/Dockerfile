FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY collector/ ./collector/

# Verify code presence (for debugging)
RUN ls -la /app && ls -la /app/collector/

# Create a non-root user (optional for prod)
RUN useradd -m -u 1000 collector && chown -R collector:collector /app
USER collector

CMD ["python", "-m", "collector.main"]

