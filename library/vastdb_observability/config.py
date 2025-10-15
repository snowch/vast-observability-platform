"""
Updated configuration to use bucket instead of database.

Replace library/vastdb_observability/config.py with this implementation.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class ProcessorConfig(BaseSettings):
    """Configuration for processors and exporters."""
    
    model_config = ConfigDict(env_prefix="", env_file=".env")

    # VAST Database connection (updated to use bucket)
    # endpoint must include http:// or https:// (e.g., http://vast.example.com:5432)
    vast_endpoint: str = "http://localhost:5432"
    vast_access_key: str = "your-access-key"
    vast_secret_key: str = "your-secret-key"
    vast_bucket: str = "observability"  # Changed from vast_database
    vast_schema: str = "observability"

    # Processing options
    enable_enrichment: bool = True
    enable_aggregation: bool = False
    aggregation_window: str = "5m"
    max_batch_size: int = 1000
    max_batch_age_seconds: int = 30

    # Data quality
    validate_data: bool = True
    drop_invalid: bool = False