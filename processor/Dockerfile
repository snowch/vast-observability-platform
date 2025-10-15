FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for librdkafka
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# --- CORRECTED PATH ---
# Copy requirements.txt from the 'processor' directory within the build context
COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CORRECTED PATH ---
# Copy the processor's application code
COPY processor/processor/ ./processor/

# --- CORRECTED PATH ---
# Copy the library from the root of the build context
COPY library/ ./library/
RUN pip install ./library/

# Create and switch to a non-root user
RUN useradd -m -u 1000 processor && chown -R processor:processor /app
USER processor

# Set the command to run the application
CMD ["python", "-m", "processor.main"]