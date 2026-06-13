import time
import pytest

# I would start with lightweight performance smoke checks in CI, then add deeper load and
# resilience tests for production candidates.

@pytest.mark.runtime
def test_health_endpoint_performance_smoke(api):
    start = time.perf_counter()
    response = api.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200, response.text
    assert elapsed_ms < 500, f"health endpoint took {elapsed_ms:.2f} ms:"
