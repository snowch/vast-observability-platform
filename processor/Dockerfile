FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for librdkafka
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the processor application code
COPY processor/ ./processor/

# Copy the library code to be installed
COPY library/ ./library/
RUN pip install ./library/

# Create a non-root user
RUN useradd -m -u 1000 processor && chown -R processor:processor /app
USER processor

CMD ["python", "-m", "processor.main"]
