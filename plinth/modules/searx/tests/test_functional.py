# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for searx app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.searx, pytest.mark.sso]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'searx')
    yield
    functional.login(session_browser)
    functional.app_disable(session_browser, 'searx')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'searx')

    functional.app_enable(session_browser, 'searx')
    assert functional.is_available(session_browser, 'searx')
    _is_search_form_visible(session_browser)

    functional.app_disable(session_browser, 'searx')
    assert not functional.is_available(session_browser, 'searx')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore."""
    functional.app_enable(session_browser, 'searx')
    functional.backup_create(session_browser, 'searx', 'test_searx')
    functional.backup_restore(session_browser, 'searx', 'test_searx')
    assert functional.is_available(session_browser, 'searx')


def test_public_access(session_browser):
    """Test enabling public access."""
    functional.app_enable(session_browser, 'searx')

    # Enable public access
    _enable_public_access(session_browser)
    functional.logout(session_browser)
    assert functional.is_visible_on_front_page(session_browser, 'searx')
    assert functional.is_available(session_browser, 'searx')

    # Disable public access
    functional.login(session_browser)
    _disable_public_access(session_browser)
    functional.logout(session_browser)
    assert not functional.is_visible_on_front_page(session_browser, 'searx')
    assert not functional.is_available(session_browser, 'searx')


def test_preserve_public_access_setting(session_browser):
    """Test that public access setting is preserved when disabling and
    re-enabling the app."""
    functional.login(session_browser)
    functional.app_enable(session_browser, 'searx')
    _enable_public_access(session_browser)

    functional.app_disable(session_browser, 'searx')
    functional.app_enable(session_browser, 'searx')
    functional.logout(session_browser)

    assert functional.is_visible_on_front_page(session_browser, 'searx')
    assert functional.is_available(session_browser, 'searx')


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
