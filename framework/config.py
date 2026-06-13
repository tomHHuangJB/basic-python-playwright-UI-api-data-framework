import os
from dataclasses import dataclass

@dataclass(frozen=True)  # Creates an immutable config value object so runtime settings cannot be changed accidentally.
class RuntimeConfig:
    app_url: str
    api_base_url: str
    deployment_id: str
    customer_id: str
    timeout_seconds: int = 10


def load_config() -> RuntimeConfig:  # The arrow declares this function returns a RuntimeConfig object.
    return RuntimeConfig(
        app_url=os.getenv("APP_URL", "http://localhost:5173").rstrip("/"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:3001").rstrip("/"),
        deployment_id=os.getenv("DEPLOYMENT_ID", "local-practice"),
        customer_id=os.getenv("CUSTOMER_ID", "practice-customer"),
    )
