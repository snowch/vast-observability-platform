FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the simulator package
COPY simulator/ ./simulator/

# Verify files
RUN ls -la /app && ls -la /app/simulator/

# Create non-root user
RUN useradd -m -u 1000 simulator && chown -R simulator:simulator /app
USER simulator

CMD ["python", "-m", "simulator.main"]
