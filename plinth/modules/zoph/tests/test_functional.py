# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for zoph app.
"""

from pytest_bdd import given, parsers, scenarios

from plinth.tests import functional

scenarios('zoph.feature')


@given(parsers.parse('the zoph application is setup'))
def _zoph_is_setup(session_browser):
    """Click setup button on the setup page."""
    functional.nav_to_module(session_browser, 'zoph')
    button = session_browser.find_by_css('input[name="zoph_setup"]')
    if button:
        functional.submit(session_browser, element=button)
