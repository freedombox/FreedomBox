# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for searx app.
"""

from pytest_bdd import given, scenarios, when

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
