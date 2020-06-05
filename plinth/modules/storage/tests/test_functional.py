# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for storage app.
"""

from pytest_bdd import given, parsers, scenarios, then

from plinth.tests import functional

scenarios('storage.feature')


@then('the root disk should be shown')
def storage_root_disk_is_shown(session_browser):
    assert _is_root_disk_shown(session_browser)


@given(parsers.parse("I'm on the {name:w} page"))
def go_to_module(session_browser, name):
    functional.nav_to_module(session_browser, name)


def _is_root_disk_shown(browser):
    table_cells = browser.find_by_tag('td')
    return any(cell.text == '/' for cell in table_cells)
