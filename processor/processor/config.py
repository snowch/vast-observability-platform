from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-ingestion:9092"
    KAFKA_GROUP_ID: str = "vastdb_processor"
    KAFKA_TOPICS: str = "otel-metrics,raw-logs,raw-queries,otlp-logs"

    # VAST Database Configuration
    VAST_ENDPOINT: str = "http://localhost:5432"
    VAST_ACCESS_KEY: str = "your-access-key"
    VAST_SECRET_KEY: str = "your-secret-key"
    VAST_BUCKET: str = "observability"

    max_batch_size: int = 100
    max_batch_age_seconds: int = 10
    enable_enrichment: bool = True
    enable_aggregation: bool = False
    aggregation_window: str = "5m"
    validate_data: bool = True
    drop_invalid: bool = False


    # Pydantic settings to load from a .env file
    class Config:
        env_file = ".env"
