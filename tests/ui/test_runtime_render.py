import pytest
from _pytest.config import Config
from playwright.sync_api import Page, expect

from framework.runtime_errors import RuntimeErrors


# For generated UI, I would always check that the app renders without browser exceptions, console errors,
# and HTTP 5xx responses. This catches many runtime issues that static checks miss.

# I do not only check that a page is visible. I also capture browser console errors, page exceptions,
# and failed network responses because generated apps can render partially while still failing at runtime.
@pytest.mark.smoke
@pytest.mark.ui
def test_app_renders_without_browser_runtime_error(page: Page, config: Config):
    errors = RuntimeErrors();

    page.on("console", lambda message: errors.console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.page_errors.append(str(error)))
    page.on(
        "response",
        lambda response: errors.failed_requests.append(f"{response.status} {response.url}") if response.status >= 500 else None,
    )

    page.goto(config.app_url)
    expect(page.locator("body")).to_be_visible()

    assert not errors.has_errors(), errors.summary()