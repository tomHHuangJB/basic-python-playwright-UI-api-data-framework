# Python + Playwright Hands-On Refresh

## Local Practice Repo

Create a practice repo:

```bash
mkdir -p /Users/tomhuang/tmp/python-playwright-practice
cd /Users/tomhuang/tmp/python-playwright-practice
python3 -m venv .venv
. .venv/bin/activate
pip install pytest pytest-playwright requests pytest-html pydantic
python -m playwright install chromium
mkdir -p framework tests/ui tests/api tests/runtime reports
touch framework/__init__.py
```

Create `pytest.ini`:

```bash
cat > pytest.ini <<'EOF'
[pytest]
testpaths = tests
addopts = -q --html=reports/report.html --self-contained-html
markers =
    smoke: fast production-readiness checks
    api: API/runtime checks
    ui: Playwright browser checks
    runtime: app startup, logs, metrics, and runtime validation
EOF
```

## Environment Variables

LocalAutomationApp URLs are the defaults in `framework/config.py`. Set `APP_URL` and `API_BASE_URL` only when overriding the target app or API.

Start LocalAutomationApp if using it as the SUT:

```bash
cd /Users/tomhuang/prog/LocalAutomationApp
docker compose --profile stable up --build --force-recreate --remove-orphans
```

Use `--force-recreate --remove-orphans` when you want a clean container run from the current Docker Compose definition.

## Framework Config

Create `framework/config.py`:

```bash
cat > framework/config.py <<'EOF'
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    app_url: str
    api_base_url: str
    deployment_id: str
    customer_id: str
    timeout_seconds: int = 10


def load_config() -> RuntimeConfig:
    return RuntimeConfig(
        app_url=os.getenv("APP_URL", "http://localhost:5173").rstrip("/"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:3001").rstrip("/"),
        deployment_id=os.getenv("DEPLOYMENT_ID", "local-practice"),
        customer_id=os.getenv("CUSTOMER_ID", "practice-customer"),
    )
EOF
```

Interview talking point:

Configuration must be environment-driven because generated apps and customer deployments will have different URLs, auth modes, and runtime metadata.

## API Client

Create `framework/api_client.py`:

```bash
cat > framework/api_client.py <<'EOF'
import requests


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get(self, path: str, **kwargs):
        return self.session.get(
            f"{self.base_url}{path}",
            timeout=self.timeout_seconds,
            **kwargs,
        )

    def post(self, path: str, json=None, headers=None, **kwargs):
        return self.session.post(
            f"{self.base_url}{path}",
            json=json,
            headers=headers,
            timeout=self.timeout_seconds,
            **kwargs,
        )
EOF
```

## Runtime Failure Collector

Create `framework/runtime_errors.py`:

```bash
cat > framework/runtime_errors.py <<'EOF'
from dataclasses import dataclass, field


@dataclass
class RuntimeErrors:
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        return bool(self.console_errors or self.page_errors or self.failed_requests)

    def summary(self) -> dict[str, list[str]]:
        return {
            "console_errors": self.console_errors,
            "page_errors": self.page_errors,
            "failed_requests": self.failed_requests,
        }
EOF
```

Interview talking point:

For AI-generated apps, a page that visually loads can still be broken. I collect console errors, page exceptions, and failed network requests as runtime quality signals.

## Test Fixtures

Create `tests/conftest.py`:

```bash
cat > tests/conftest.py <<'EOF'
import pytest

from framework.api_client import ApiClient
from framework.config import RuntimeConfig, load_config


@pytest.fixture(scope="session")
def config() -> RuntimeConfig:
    return load_config()


@pytest.fixture
def api(config: RuntimeConfig) -> ApiClient:
    return ApiClient(config.api_base_url, config.timeout_seconds)
EOF
```

## API Runtime Smoke Test

Create `tests/api/test_health_and_system.py`:

```bash
cat > tests/api/test_health_and_system.py <<'EOF'
import pytest


@pytest.mark.smoke
@pytest.mark.api
def test_api_health(api):
    response = api.get("/health")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


@pytest.mark.api
def test_system_runtime_metadata(api):
    response = api.get("/api/time-skew")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "serverTime" in body
    assert "skewMs" in body
EOF
```

Note:

The first runtime gate is simple: can the generated app or service respond to health/system endpoints reliably?

## Playwright Runtime Smoke Test

Create `tests/ui/test_runtime_render.py`:

```bash
cat > tests/ui/test_runtime_render.py <<'EOF'
import pytest
from playwright.sync_api import Page, expect

from framework.runtime_errors import RuntimeErrors


@pytest.mark.smoke
@pytest.mark.ui
def test_app_renders_without_browser_runtime_errors(page: Page, config):
    errors = RuntimeErrors()

    page.on("console", lambda message: errors.console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.page_errors.append(str(error)))
    page.on(
        "response",
        lambda response: errors.failed_requests.append(f"{response.status} {response.url}") if response.status >= 500 else None,
    )

    page.goto(config.app_url)
    expect(page.locator("body")).to_be_visible()

    assert not errors.has_errors(), errors.summary()
EOF
```

Note:

For generated UI, I would always check that the app renders without browser exceptions, console errors, and HTTP 5xx responses. This catches many runtime issues that static checks miss.

## LocalAutomationApp Auth + Protected Route Practice

Create `tests/ui/test_auth_runtime.py`:

```bash
cat > tests/ui/test_auth_runtime.py <<'EOF'
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
def test_login_session_and_protected_route(page: Page, config):
    page.goto(f"{config.app_url}/auth")

    page.get_by_test_id("login-username").fill("principal.engineer")
    page.get_by_test_id("login-password").fill("demo")
    page.get_by_test_id("login-submit").click()

    expect(page.get_by_test_id("auth-status")).to_contain_text("token:")

    page.get_by_test_id("session-check").click()
    expect(page.get_by_test_id("auth-status")).to_contain_text("me:principal.engineer")

    page.goto(f"{config.app_url}/protected")
    expect(page.get_by_test_id("protected-status")).to_contain_text("authenticated")
    expect(page.get_by_test_id("protected-user")).to_contain_text("principal.engineer")
EOF
```

Note:

This demonstrates a real E2E runtime check: UI login, session verification, protected route access, and visible role/user state.

## API Data Flow Practice

Create `tests/api/test_business_data_flow.py`:

```bash
cat > tests/api/test_business_data_flow.py <<'EOF'
import time
import pytest


def order_payload(unique: str) -> dict:
    return {
        "customer": {
            "externalId": f"cust-{unique}",
            "name": "Runtime Customer",
            "email": f"runtime-{unique}@example.com",
        },
        "items": [
            {"sku": "-AAA", "quantity": 2, "unitPrice": 10.5},
            {"sku": "-BBB", "quantity": 3, "unitPrice": 7},
        ],
        "payment": {
            "provider": "test-pay",
            "authorizationCode": "AUTH-",
        },
        "currency": "USD",
    }


@pytest.mark.api
def test_api_to_database_to_downstream_runtime_flow(api):
    reset = api.post("/api/reset", json={})
    assert reset.status_code == 200, reset.text

    unique = str(int(time.time() * 1000))
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
    assert loaded.json()["totalAmount"] == 42

    integrity = api.get(f"/api/business-flow/orders/{order_id}/integrity")
    assert integrity.status_code == 200, integrity.text
    assert integrity.json()["passed"] is True

    downstream = api.get(f"/api/downstream/consumer-events/{correlation_id}")
    assert downstream.status_code == 200, downstream.text
    assert downstream.json()["events"][0]["payload"]["totalAmount"] == 42
EOF
```

Note:

This is the exact production-readiness pattern I would use for generated services: API response, persisted/reconstructed state, integrity check, and downstream event validation with a correlation ID.

For unique test data, `uuid.uuid4()` is usually better than `str(int(time.time() * 1000))` when the goal is uniqueness rather than time ordering.

Timestamp-based IDs are shorter, easier to scan in logs, and roughly sortable by creation time. They are fine for simple local tests that run one at a time. The downside is that they can collide when multiple tests create data in the same millisecond, especially in parallel test runs, and they depend on system clock behavior.

UUID-based IDs are extremely unlikely to collide, work better for parallel tests, do not depend on timestamp precision, and clearly communicate that the test needs a unique value. The tradeoff is that UUIDs are longer, less readable in logs, and not naturally time-sortable.

For this API flow test, `uuid.uuid4()` is the better default because the unique value is only used to avoid data collisions across generated customers, emails, and correlation IDs.

## SQL/ETL/Warehouse Runtime Validation Practice

Create `tests/api/test_data_sql_etl_runtime.py`:

```bash
cat > tests/api/test_data_sql_etl_runtime.py <<'EOF'
import time
import pytest


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
        "currency": "USD",
    }


@pytest.mark.api
@pytest.mark.runtime
def test_etl_and_warehouse_fact_runtime_validation(api):
    assert api.post("/api/reset", json={}).status_code == 200

    unique = str(int(time.time() * 1000))
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
    assert db_rows.json()["tables"]["orders"][0]["correlation_id"] == correlation_id

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
EOF
```

Note:

For generated applications with data flows, I would validate source payload, normalized rows, reconciliation query, ETL run metadata, and warehouse facts. That proves runtime behavior beyond the first API call.

## Performance Smoke Practice

Create `tests/runtime/test_performance_smoke.py`:

```bash
cat > tests/runtime/test_performance_smoke.py <<'EOF'
import time
import pytest


@pytest.mark.runtime
def test_health_endpoint_performance_smoke(api):
    start = time.perf_counter()
    response = api.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200, response.text
    assert elapsed_ms < 500, f"health endpoint took {elapsed_ms:.2f}ms"
EOF
```

Note:

I would start with lightweight performance smoke checks in CI, then add deeper load and resilience tests for production candidates.

## Runtime Quality Score

Create `framework/quality_score.py`:

```bash
cat > framework/quality_score.py <<'EOF'
from dataclasses import dataclass


@dataclass(frozen=True)
class QualitySignals:
    health_passed: bool
    ui_passed: bool
    api_passed: bool
    runtime_error_count: int
    p95_latency_ms: float


def quality_score(signals: QualitySignals) -> int:
    score = 100
    if not signals.health_passed:
        score -= 35
    if not signals.ui_passed:
        score -= 20
    if not signals.api_passed:
        score -= 25
    score -= min(signals.runtime_error_count * 5, 20)
    if signals.p95_latency_ms > 1000:
        score -= 10
    return max(score, 0)
EOF
```

Create `tests/runtime/test_quality_score.py`:

```bash
cat > tests/runtime/test_quality_score.py <<'EOF'
from framework.quality_score import QualitySignals, quality_score


def test_quality_score_penalizes_runtime_failures():
    assert quality_score(QualitySignals(True, True, True, 0, 250)) == 100
    assert quality_score(QualitySignals(True, False, True, 2, 250)) == 70
    assert quality_score(QualitySignals(False, True, True, 0, 250)) == 65
EOF
```

Note:

I would not rely only on raw pass/fail. I would also track quality signals and summarize them by generated app, framework, customer deployment, and failure category.

## Run Commands

Run all:

```bash
cd /Users/tomhuang/tmp/-python-playwright-practice
. .venv/bin/activate
pytest
```

Run only smoke:

```bash
pytest -m smoke
```

Run only API:

```bash
pytest -m api
```

Run only UI:

```bash
pytest -m ui --headed
```

Run a single test:

```bash
pytest tests/api/test_business_data_flow.py -q
```

## Daily Practice Plan

### Day 1: Python Framework Basics

Type from memory:

1. `RuntimeConfig`
2. `ApiClient`
3. pytest fixtures
4. health test

Interview answer to practice:

I use Python as the orchestration layer because it is strong for API calls, file/log processing, configuration, data validation, and CI glue.

### Day 2: Playwright Runtime Errors

Type from memory:

1. `page.on("console", ...)`
2. `page.on("pageerror", ...)`
3. `page.on("response", ...)`
4. runtime error assertion

Interview answer to practice:

I do not only check that a page is visible. I also capture browser console errors, page exceptions, and failed network responses because generated apps can render partially while still failing at runtime.

### Day 3: API + Data + Downstream

Type from memory:

1. create payload
2. POST with correlation ID
3. retrieve order
4. integrity endpoint
5. downstream event endpoint

Interview answer to practice:

For distributed workflows, I verify the entire effect of an operation, not only the first response. I use correlation IDs to connect API calls, persisted state, downstream events, and logs.

### Day 4: SQL/ETL/Warehouse

Type from memory:

1. DB inspection endpoint
2. named reconciliation query
3. ETL run
4. ETL run status
5. warehouse fact validation

Interview answer to practice:

For generated apps with data pipelines, I validate source-to-target behavior: API input, normalized rows, reconciliation totals, ETL run metadata, and target facts.

### Day 5: CI/CD And Quality Score

Type from memory:

1. quality signals dataclass
2. quality score function
3. pytest marker commands
4. artifact/report command

Interview answer to practice:

CI should produce evidence. A generated app should not be considered production-ready if it cannot build, start, pass health checks, pass critical UI/API flows, stay free of runtime exceptions, and meet baseline performance thresholds.

##  Interview One-Minute Technical Pitch

I would build a Python-driven runtime validation harness with Playwright for browser behavior and Python for API, data, log, metrics, and CI orchestration. It would receive metadata for each generated app or customer deployment, run universal checks like build/startup/health, then select capability-specific checks for UI, API, auth, CRUD, persistence, downstream integrations, and performance. It would automatically flag console errors, page exceptions, HTTP 5xx responses, failed workflows, slow endpoints, and backend exceptions. The results would be grouped by deployment, framework, app type, and failure category so the AI team can improve the generator based on real runtime data.
