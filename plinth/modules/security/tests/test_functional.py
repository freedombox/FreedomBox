# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for security app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('security.feature')


@given(parsers.parse('restricted console logins are {enabled}'))
def security_given_enable_restricted_logins(session_browser, enabled):
    should_enable = (enabled == 'enabled')
    _enable_restricted_logins(session_browser, should_enable)


@when(parsers.parse('I {enable} restricted console logins'))
def security_enable_restricted_logins(session_browser, enable):
    should_enable = (enable == 'enable')
    _enable_restricted_logins(session_browser, should_enable)


@then(parsers.parse('restricted console logins should be {enabled}'))
def security_assert_restricted_logins(session_browser, enabled):
    enabled = (enabled == 'enabled')
    assert _get_restricted_logins(session_browser) == enabled


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
