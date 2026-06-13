import uuid

import pytest


# This is the exact production-readiness pattern I would use for generated services:
# API response, persisted/reconstructed state, integrity check, and downstream event validation with a correlation ID.

def order_payload(unique: str) -> dict:
    return {
        "customer": {
            "externalId": f"cust-{unique}",
            "name": "Runtime Customer",
            "email": f"runtime-{unique}@example.com",
        },
        "items": [
            {"sku": "BLITZY-AAA", "quantity": 2, "unitPrice": 10.5},
            {"sku": "BLITZY-BBB", "quantity": 3, "unitPrice": 7},
        ],
        "payment": {
            "provider": "test-pay",
            "authorizationCode":"AUTH-BLITZY",
        },
        "currency": "USD",
    }

@pytest.mark.api
def test_api_to_database_to_downstream_runtime_flow(api):
    reset = api.post("/api/reset", json={})
    assert reset.status_code == 200, reset.text

    unique = str(uuid.uuid4())
    correlation_id = f"corr-{unique}"

    created = api.post(
        "/api/business-flow/orders",
        json=order_payload(unique),
        headers={"X-Correlation-ID": correlation_id},
    )

    assert created.status_code == 201, created.text
    created_body = created.json()
    order_id = created_body["orderId"]

    loaded = api.get(f"/api/business-flow/orders/{order_id}")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() ["totalAmount"] == 42

    integrity = api.get(f"/api/business-flow/orders/{order_id}/integrity")
    assert integrity.status_code == 200, integrity.text
    assert integrity.json() ["passed"] is True

    downstream = api.get(f"/api/downstream/consumer-events/{correlation_id}")
    assert downstream.status_code == 200, downstream.text
    assert downstream.json() ["events"][0]["payload"]["totalAmount"] == 42
