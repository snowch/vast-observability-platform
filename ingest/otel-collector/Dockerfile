# Use the base OpenTelemetry Collector image
FROM otel/opentelemetry-collector-contrib:0.91.0

# Copy your local config file into the container
COPY otel-collector-config.yaml /etc/otel-collector-config.yaml

# Run as root (safe here since it's local-only and avoids permission issues)
USER 0

# Default command (same as before)
CMD ["--config=/etc/otel-collector-config.yaml"]
