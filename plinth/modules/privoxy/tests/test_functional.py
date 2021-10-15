# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for privoxy app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.privoxy]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'privoxy')
    yield
    functional.app_disable(session_browser, 'privoxy')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'privoxy')

    functional.app_enable(session_browser, 'privoxy')
    assert functional.service_is_running(session_browser, 'privoxy')

    functional.app_disable(session_browser, 'privoxy')
    assert functional.service_is_not_running(session_browser, 'privoxy')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'privoxy')
    functional.backup_create(session_browser, 'privoxy', 'test_privoxy')
    functional.backup_restore(session_browser, 'privoxy', 'test_privoxy')
    assert functional.service_is_running(session_browser, 'privoxy')
