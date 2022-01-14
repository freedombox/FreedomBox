# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for config app.
"""

import pytest
from plinth.tests import functional

pytestmark = [
    pytest.mark.system, pytest.mark.essential, pytest.mark.domain,
    pytest.mark.config
]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_change_hostname(session_browser):
    """Test changing the hostname."""
    _set_hostname(session_browser, 'mybox')
    assert _get_hostname(session_browser) == 'mybox'


def test_change_domain_name(session_browser):
    """Test changing the domain name."""
    functional.set_domain_name(session_browser, 'mydomain.example')
    assert _get_domain_name(session_browser) == 'mydomain.example'

    # Capitalization is ignored.
    functional.set_domain_name(session_browser, 'Mydomain.example')
    assert _get_domain_name(session_browser) == 'mydomain.example'


def test_change_home_page(session_browser):
    """Test changing webserver home page."""
    functional.install(session_browser, 'syncthing')
    functional.app_enable(session_browser, 'syncthing')
    _set_home_page(session_browser, 'syncthing')

    _set_home_page(session_browser, 'plinth')
    assert _check_home_page_redirect(session_browser, 'plinth')


def _get_hostname(browser):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_id('id_hostname').value


def _set_hostname(browser, hostname):
    functional.nav_to_module(browser, 'config')
    browser.find_by_id('id_hostname').fill(hostname)
    update_setup = browser.find_by_css('.btn-primary')
    functional.submit(browser, element=update_setup)


def _get_domain_name(browser):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_id('id_domainname').value


def _set_home_page(browser, home_page):
    if 'plinth' not in home_page and 'apache' not in home_page:
        home_page = 'shortcut-' + home_page

    functional.nav_to_module(browser, 'config')
    drop_down = browser.find_by_id('id_homepage')
    drop_down.select(home_page)
    update_setup = browser.find_by_css('.btn-primary')
    functional.submit(browser, element=update_setup)


def _check_home_page_redirect(browser, app_name):
    functional.visit(browser, '/')
    return browser.find_by_xpath(
        "//a[contains(@href, '/plinth/') and @title='FreedomBox']")
