# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for zoph app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.zoph]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'zoph')
    _zoph_is_setup(session_browser)
    yield
    functional.app_disable(session_browser, 'zoph')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'zoph')

    functional.app_enable(session_browser, 'zoph')
    assert functional.app_is_enabled(session_browser, 'zoph')

    functional.app_disable(session_browser, 'zoph')
    assert not functional.app_is_enabled(session_browser, 'zoph')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'zoph')
    functional.backup_create(session_browser, 'zoph', 'test_zoph')
    functional.backup_restore(session_browser, 'zoph', 'test_zoph')
    assert functional.app_is_enabled(session_browser, 'zoph')


def _zoph_is_setup(session_browser):
    """Click setup button on the setup page."""
    functional.nav_to_module(session_browser, 'zoph')
    button = session_browser.find_by_css('input[name="zoph_setup"]')
    if button:
        functional.submit(session_browser, element=button)
