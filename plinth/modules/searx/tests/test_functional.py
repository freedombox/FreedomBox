# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for searx app.
"""

from pytest_bdd import given, scenarios, then, when

from plinth.tests import functional

scenarios('searx.feature')


@given('public access is enabled in searx')
def searx_public_access_enabled(session_browser):
    _enable_public_access(session_browser)


@when('I enable public access in searx')
def searx_enable_public_access(session_browser):
    _enable_public_access(session_browser)


@when('I disable public access in searx')
def searx_disable_public_access(session_browser):
    _disable_public_access(session_browser)


@then('the search form should be visible')
def is_searx_search_form_visible(session_browser):
    _is_search_form_visible(session_browser)


def _enable_public_access(browser):
    """Enable Public Access in SearX"""
    functional.nav_to_module(browser, 'searx')
    browser.find_by_id('id_public_access').check()
    functional.submit(browser, form_class='form-configuration')


def _disable_public_access(browser):
    """Enable Public Access in SearX"""
    functional.nav_to_module(browser, 'searx')
    browser.find_by_id('id_public_access').uncheck()
    functional.submit(browser, form_class='form-configuration')


def _is_search_form_visible(browser):
    """Checks whether the search box is shown in the Searx web interface."""
    searx_app_url = functional.config['DEFAULT']['url'] + '/searx'
    browser.visit(searx_app_url)
    assert browser.find_by_id("search_form")
