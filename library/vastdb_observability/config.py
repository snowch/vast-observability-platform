from pydantic_settings import BaseSettings
from typing import Optional


class ProcessorConfig(BaseSettings):
    """Configuration for processors and exporters."""

    # VAST Database connection
    vast_host: str = "localhost"
    vast_port: int = 5432
    vast_database: str = "observability"
    vast_username: str = "vast_user"
    vast_password: str = "vast_password"
    vast_schema: str = "public"

    # Processing options
    enable_enrichment: bool = True
    enable_aggregation: bool = False
    aggregation_window: str = "5m"
    max_batch_size: int = 1000
    max_batch_age_seconds: int = 30

    # Data quality
    validate_data: bool = True
    drop_invalid: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
