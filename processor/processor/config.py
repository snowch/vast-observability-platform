from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-ingestion:9092"
    KAFKA_GROUP_ID: str = "vastdb_processor"
    KAFKA_TOPICS: str = "otel-metrics,raw-logs,raw-queries"

    # VAST Database Configuration
    VAST_ENDPOINT: str = "http://localhost:5432"
    VAST_ACCESS_KEY: str = "your-access-key"
    VAST_SECRET_KEY: str = "your-secret-key"
    VAST_BUCKET: str = "observability"

    # --- FIX ---
    # Add the missing batching settings that the BatchProcessor requires.
    # These names must match the attributes expected by the ProcessorConfig
    # in the library (max_batch_size, max_batch_age_seconds).
    max_batch_size: int = 100
    max_batch_age_seconds: int = 10

    # Pydantic settings to load from a .env file
    class Config:
        env_file = ".env"