import pytest
from vastdb_observability.config import ProcessorConfig


@pytest.fixture
def config():
    """Test configuration."""
    return ProcessorConfig(
        vast_host="localhost",
        vast_port=5432,
        vast_database="test_db",
        vast_username="test_user",
        vast_password="test_pass",
    )
