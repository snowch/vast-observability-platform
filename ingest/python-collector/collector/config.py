from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "monitor_user"
    POSTGRES_PASSWORD: str = "monitor_password"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-ingestion:9092"
    COLLECTION_INTERVAL: int = 30
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
