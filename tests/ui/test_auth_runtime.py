import pytest
from playwright.sync_api import Page, expect

# This demonstrates a real E2E runtime check: UI login, session verification, protected route access,
# and visible role/user state.

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
