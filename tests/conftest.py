import pytest

from framework.api_client import ApiClient
from framework.config import RuntimeConfig, load_config

@pytest.fixture(scope="session")
def config() -> RuntimeConfig:
    return load_config()

@pytest.fixture
def api(config: RuntimeConfig) -> ApiClient:
    return ApiClient(config.api_base_url, config.timeout_seconds)

