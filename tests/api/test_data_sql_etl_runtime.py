import uuid
import pytest

# For generated applications with data flows, I would validate source payload, normalized rows, reconciliation query,
# ETL run metadata, and warehouse facts. That proves runtime behavior beyond the first API call.

def order_payload(unique: str) -> dict:
    return {
        "customer": {
            "externalId": f"cust-etl-{unique}",
            "name": "ETL Runtime Customer",
            "email": f"etl-runtime-{unique}@example.com",
        },
        "items": [
            {"sku": "ETL-AAA", "quantity": 4, "unitPrice": 3.25},
            {"sku": "ETL-BBB", "quantity": 1, "unitPrice": 9.5},
        ],
        "payment": {"provider": "warehouse-pay", "authorizationCode": "AUTH-ETL"},
        "currency":"USD",
    }

@pytest.mark.api
@pytest.mark.runtime
def test_etl_and_warehouse_fact_runtime_validation(api):
    assert api.post("/api/reset", json={}).status_code == 200

    unique = str(uuid.uuid4())
    correlation_id = f"corr-etl-{unique}"

    created = api.post(
        "/api/business-flow/orders",
        json=order_payload(unique),
        headers={"X-Correlation-ID": correlation_id},

    )
    assert created.status_code == 201, created.text
    body = created.json()
    # Validate the source API payload returned the identifiers needed to trace the order through later systems.
    order_id = body["orderId"]
    order_number = body["orderNumber"]

    # Validate normalized database rows, proving the first API call persisted relational data correctly.
    db_rows = api.get(f"/api/test/db/orders/{order_id}/tables")

    assert db_rows.status_code == 200, db_rows.text
    assert db_rows.json() ["tables"] ["orders"] [0] ["correlation_id"] == correlation_id

    # Validate a reconciliation query, proving cross-table business integrity beyond the create response.
    reconciliation = api.get("/api/test/db/query?name=business_order_integrity")
    assert reconciliation.status_code == 200, reconciliation.text
    assert any(row["order_id"] == order_id for row in reconciliation.json()["rows"])

    # Validate ETL run metadata, proving the downstream transformation job completed without runtime errors.
    etl = api.post("/api/etl/run/orders", json={})
    assert etl.status_code == 201, etl.text
    run = etl.json()["run"]
    assert run["status"] == "COMPLETED"
    assert run["error_count"] == 0

    # Validate warehouse facts, proving the order was transformed into analytics-ready data after the API call.
    warehouse = api.get(f"/api/warehouse/orders/{order_number}")
    assert warehouse.status_code == 200, warehouse.text
    fact = warehouse.json()
    assert fact["source_order_id"] == order_id
    assert fact["correlation_id"] == correlation_id
    assert fact["data_quality_status"] == "PASS"
