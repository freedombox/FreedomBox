# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mumble app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.mumble]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'mumble')
    yield
    functional.app_disable(session_browser, 'mumble')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'mumble')

    functional.app_enable(session_browser, 'mumble')
    assert functional.service_is_running(session_browser, 'mumble')

    functional.app_disable(session_browser, 'mumble')
    assert functional.service_is_not_running(session_browser, 'mumble')


# TODO: Improve this to actually check that data such as rooms, identity or
# certificates are restored.
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'mumble')
    functional.backup_create(session_browser, 'mumble', 'test_mumble')
    functional.backup_restore(session_browser, 'mumble', 'test_mumble')
    assert functional.service_is_running(session_browser, 'mumble')
