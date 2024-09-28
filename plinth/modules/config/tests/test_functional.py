# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for config app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.config]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_change_home_page(session_browser):
    """Test changing webserver home page."""
    functional.install(session_browser, 'syncthing')
    functional.app_enable(session_browser, 'syncthing')
    _set_home_page(session_browser, 'syncthing')

    _set_home_page(session_browser, 'plinth')
    assert _check_home_page_redirect(session_browser, 'plinth')


def _set_home_page(browser, home_page):
    if 'plinth' not in home_page and 'apache' not in home_page:
        home_page = 'shortcut-' + home_page

    functional.nav_to_module(browser, 'config')
    drop_down = browser.find_by_id('id_homepage')
    drop_down.select(home_page)
    functional.submit(browser, form_class='form-configuration')


def _check_home_page_redirect(browser, app_name):
    functional.visit(browser, '/')
    return browser.find_by_xpath(
        "//a[contains(@href, '/plinth/') and @title='FreedomBox']")
