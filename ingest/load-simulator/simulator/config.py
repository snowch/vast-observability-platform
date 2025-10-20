from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL Settings
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    
    # OTel Collector Syslog Settings
    OTEL_COLLECTOR_HOST: str = "otel-collector"
    OTEL_COLLECTOR_SYSLOG_PORT: int = 5140

    # Workload Generation Settings
    QUERY_RATE: int = 10
    SLOW_QUERY_PROBABILITY: float = 0.1
    WRITE_PROBABILITY: float = 0.3
    SYSLOG_PROBABILITY: float = 0.2  # New: 20% chance to send a syslog message

    class Config:
        env_file = ".env"