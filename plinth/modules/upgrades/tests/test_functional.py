# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for upgrades app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('upgrades.feature')


@given(parsers.parse('automatic upgrades are {enabled:w}'))
def upgrades_given_enable_automatic(session_browser, enabled):
    should_enable = (enabled == 'enabled')
    _enable_automatic(session_browser, should_enable)


@when(parsers.parse('I {enable:w} automatic upgrades'))
def upgrades_enable_automatic(session_browser, enable):
    should_enable = (enable == 'enable')
    _enable_automatic(session_browser, should_enable)


@then(parsers.parse('automatic upgrades should be {enabled:w}'))
def upgrades_assert_automatic(session_browser, enabled):
    should_be_enabled = (enabled == 'enabled')
    assert _get_automatic(session_browser) == should_be_enabled


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

    functional.submit(browser)


def _get_automatic(browser):
    """Return whether automatic software upgrades is enabled."""
    functional.nav_to_module(browser, 'upgrades')
    return browser.find_by_name('auto_upgrades_enabled').first.checked
