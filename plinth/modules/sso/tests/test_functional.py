# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for sso app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.sso]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'syncthing')
    functional.app_enable(session_browser, 'syncthing')
    yield
    functional.app_disable(session_browser, 'syncthing')


def test_app_access(session_browser):
    """Test that only logged-in users can access Syncthing web interface."""
    functional.logout(session_browser)
    functional.access_url(session_browser, 'syncthing')
    assert functional.is_login_prompt(session_browser)

    functional.login(session_browser)
    functional.access_url(session_browser, 'syncthing')
    assert functional.is_available(session_browser, 'syncthing')
