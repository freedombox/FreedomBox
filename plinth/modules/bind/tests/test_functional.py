# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for bind app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('bind.feature')


@given(parsers.parse('bind DNSSEC is {enable:w}'))
def bind_given_enable_dnssec(session_browser, enable):
    should_enable = (enable == 'enabled')
    _enable_dnssec(session_browser, should_enable)


@when(parsers.parse('I {enable:w} bind DNSSEC'))
def bind_enable_dnssec(session_browser, enable):
    should_enable = (enable == 'enable')
    _enable_dnssec(session_browser, should_enable)


@then(parsers.parse('bind DNSSEC should be {enabled:w}'))
def bind_assert_dnssec(session_browser, enabled):
    assert _get_dnssec(session_browser) == (enabled == 'enabled')


def _enable_dnssec(browser, enable):
    """Enable/disable DNSSEC in bind configuration."""
    functional.nav_to_module(browser, 'bind')
    if enable:
        browser.check('enable_dnssec')
    else:
        browser.uncheck('enable_dnssec')

    functional.submit(browser, form_class='form-configuration')


def _get_dnssec(browser):
    """Return whether DNSSEC is enabled/disabled in bind configuration."""
    functional.nav_to_module(browser, 'bind')
    return browser.find_by_name('enable_dnssec').first.checked
