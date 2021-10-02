# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for security app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.security]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_restricted_console_logins(session_browser):
    """Test enabling and disabling restricted console logins."""
    _enable_restricted_logins(session_browser, False)
    assert not _get_restricted_logins(session_browser)

    _enable_restricted_logins(session_browser, True)
    assert _get_restricted_logins(session_browser)


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    _enable_restricted_logins(session_browser, True)
    functional.backup_create(session_browser, 'security', 'test_security')

    _enable_restricted_logins(session_browser, False)
    functional.backup_restore(session_browser, 'security', 'test_security')

    assert _get_restricted_logins(session_browser)


def _enable_restricted_logins(browser, should_enable):
    """Enable/disable restricted logins in security module."""
    functional.nav_to_module(browser, 'security')
    if should_enable:
        browser.check('security-restricted_access')
    else:
        browser.uncheck('security-restricted_access')

    functional.submit(browser)


def _get_restricted_logins(browser):
    """Return whether restricted console logins is enabled."""
    functional.nav_to_module(browser, 'security')
    return browser.find_by_name('security-restricted_access').first.checked
