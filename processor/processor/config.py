from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-ingestion:9092"
    KAFKA_GROUP_ID: str = "vastdb_processor"
    KAFKA_TOPICS: str = "raw-logs,raw-queries"

    # VAST Database Configuration
    VAST_ENDPOINT: str = "http://localhost:5432"
    VAST_ACCESS_KEY: str = "your-access-key"
    VAST_SECRET_KEY: str = "your-secret-key"
    VAST_BUCKET: str = "observability"

    # Batching Configuration
    MAX_BATCH_SIZE: int = 100
    MAX_BATCH_AGE_SECONDS: int = 10

    class Config:
        env_file = ".env"
