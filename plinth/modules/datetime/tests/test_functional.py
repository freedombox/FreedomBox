# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for datetime app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.datetime]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_enable_disable(session_browser):
    """Test enabling the app."""
    if functional.app_can_be_disabled(session_browser, 'datetime'):
        functional.app_disable(session_browser, 'datetime')

        functional.app_enable(session_browser, 'datetime')
        assert functional.service_is_running(session_browser, 'datetime')

        functional.app_disable(session_browser, 'datetime')
        assert functional.service_is_not_running(session_browser, 'datetime')

    else:
        pytest.skip('datetime cannot be disabled.')


def test_set_timezone(session_browser):
    """Test setting the timezone."""
    _time_zone_set(session_browser, 'Africa/Abidjan')
    assert _time_zone_get(session_browser) == 'Africa/Abidjan'


@pytest.mark.backups
def test_backup_and_restore(session_browser):
    """Test backup and restore of datetime settings."""
    _time_zone_set(session_browser, 'Africa/Accra')
    functional.backup_create(session_browser, 'datetime', 'test_datetime')

    _time_zone_set(session_browser, 'Africa/Cairo')
    functional.backup_restore(session_browser, 'datetime', 'test_datetime')

    assert _time_zone_get(session_browser) == 'Africa/Accra'


def _time_zone_set(browser, time_zone):
    """Set the system time zone."""
    functional.nav_to_module(browser, 'datetime')
    browser.select('time_zone', time_zone)
    functional.submit(browser, form_class='form-configuration')


def _time_zone_get(browser):
    """Set the system time zone."""
    functional.nav_to_module(browser, 'datetime')
    return browser.find_by_name('time_zone').first.value
