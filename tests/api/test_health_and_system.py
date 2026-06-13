import pytest

# can the service respond to health/system endpoints reliably
@pytest.mark.smoke
@pytest.mark.api
def test_api_health(api):
    response =api.get("/health")
    assert response.status_code == 200, response.text
    assert response.json() ["status"] == "ok"

@pytest.mark.api
def test_system_runtime_metadata(api):
    response = api.get("/api/time-skew")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "serverTime" in body
    assert "skewMs" in body

