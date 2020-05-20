# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for help app.
"""

from pytest_bdd import scenarios, then, when

from plinth.tests import functional

scenarios('help.feature')


@when('I go to the status logs page')
def help_go_to_status_logs(session_browser):
    _go_to_status_logs(session_browser)


@then('status logs should be shown')
def help_status_logs_are_shown(session_browser):
    assert _are_status_logs_shown(session_browser)


def _go_to_status_logs(browser):
    functional.visit(browser, '/plinth/help/status-log/')


def _are_status_logs_shown(browser):
    return browser.is_text_present('Logs begin')
