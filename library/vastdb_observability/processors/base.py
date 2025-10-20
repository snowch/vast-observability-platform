from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar, Generic, Optional
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class BaseProcessor(ABC, Generic[T]):
    """Base class for all processors."""

    def __init__(self, config: Optional["ProcessorConfig"] = None):
        from vastdb_observability.config import ProcessorConfig
        self.config = config or ProcessorConfig()
        self.logger = logger.bind(processor=self.__class__.__name__)

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any], topic: str = "") -> T:
        """Normalize raw data into common schema."""
        pass

    @abstractmethod
    def enrich(self, data: T) -> T:
        """Enrich data with computed fields and metadata."""
        pass

    def validate(self, data: T) -> bool:
        """Validate data quality."""
        if not self.config.validate_data:
            return True

        try:
            return True
        except Exception as e:
            self.logger.warning("validation_failed", error=str(e))
            return False

    def process(self, raw_data: Dict[str, Any], topic: str = "", **kwargs) -> T:
        """Full processing pipeline: normalize -> enrich -> validate."""
        normalized = self.normalize(raw_data, topic=topic)

        if self.config.enable_enrichment and kwargs.get("enrich", True):
            normalized = self.enrich(normalized)

        if not self.validate(normalized):
            if self.config.drop_invalid:
                raise ValueError("Data validation failed")
            self.logger.warning("invalid_data_kept")

        return normalized