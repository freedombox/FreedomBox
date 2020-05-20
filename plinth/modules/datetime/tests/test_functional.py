# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for datetime app.
"""

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('datetime.feature')


@when(parsers.parse('I set the time zone to {time_zone:S}'))
def time_zone_set(session_browser, time_zone):
    _time_zone_set(session_browser, time_zone)


@then(parsers.parse('the time zone should be {time_zone:S}'))
def time_zone_assert(session_browser, time_zone):
    assert time_zone == _time_zone_get(session_browser)


def _time_zone_set(browser, time_zone):
    """Set the system time zone."""
    functional.nav_to_module(browser, 'datetime')
    browser.select('time_zone', time_zone)
    functional.submit(browser, form_class='form-configuration')


def _time_zone_get(browser):
    """Set the system time zone."""
    functional.nav_to_module(browser, 'datetime')
    return browser.find_by_name('time_zone').first.value
