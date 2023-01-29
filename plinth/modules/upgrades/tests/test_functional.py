# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for upgrades app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.upgrades]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)
    yield
    _enable_automatic(session_browser, False)


def test_enable_automatic_upgrades(session_browser):
    """Test enabling automatic upgrades."""
    _enable_automatic(session_browser, False)
    _enable_automatic(session_browser, True)
    assert _get_automatic(session_browser)

    _enable_automatic(session_browser, False)
    assert not _get_automatic(session_browser)


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    _enable_automatic(session_browser, True)
    functional.backup_create(session_browser, 'upgrades', 'test_upgrades')

    _enable_automatic(session_browser, False)
    functional.backup_restore(session_browser, 'upgrades', 'test_upgrades')

    assert _get_automatic(session_browser)


def _enable_automatic(browser, should_enable):
    """Enable/disable automatic software upgrades."""
    functional.nav_to_module(browser, 'upgrades')
    checkbox_element = browser.find_by_name('auto_upgrades_enabled').first
    if should_enable == checkbox_element.checked:
        return

    if should_enable:
        checkbox_element.check()
    else:
        checkbox_element.uncheck()

    functional.submit(browser, form_class='form-configuration')


def _get_automatic(browser):
    """Return whether automatic software upgrades is enabled."""
    functional.nav_to_module(browser, 'upgrades')
    return browser.find_by_name('auto_upgrades_enabled').first.checked
