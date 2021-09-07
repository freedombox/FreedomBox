# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for performance app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.performance]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'performance')
    yield
    functional.app_disable(session_browser, 'performance')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'performance')

    functional.app_enable(session_browser, 'performance')
    assert functional.service_is_running(session_browser, 'performance')

    functional.app_disable(session_browser, 'performance')
    assert functional.service_is_not_running(session_browser, 'performance')
