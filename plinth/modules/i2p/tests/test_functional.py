# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for i2p app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.i2p]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'i2p')
    yield
    functional.app_disable(session_browser, 'i2p')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'i2p')

    functional.app_enable(session_browser, 'i2p')
    assert functional.service_is_running(session_browser, 'i2p')
    assert functional.is_available(session_browser, 'i2p')

    functional.app_disable(session_browser, 'i2p')
    assert functional.service_is_not_running(session_browser, 'i2p')
    assert not functional.is_available(session_browser, 'i2p')
