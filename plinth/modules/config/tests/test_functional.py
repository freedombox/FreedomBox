# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for config app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('config.feature')


@given(parsers.parse('the home page is {app_name:w}'))
def set_home_page(session_browser, app_name):
    _set_home_page(session_browser, app_name)


@when(parsers.parse('I change the hostname to {hostname:w}'))
def change_hostname_to(session_browser, hostname):
    _set_hostname(session_browser, hostname)


@when(parsers.parse('I change the domain name to {domain:S}'))
def change_domain_name_to(session_browser, domain):
    functional.set_domain_name(session_browser, domain)


@when(parsers.parse('I change the home page to {app_name:w}'))
def change_home_page_to(session_browser, app_name):
    _set_home_page(session_browser, app_name)


@then(parsers.parse('the hostname should be {hostname:w}'))
def hostname_should_be(session_browser, hostname):
    assert _get_hostname(session_browser) == hostname


@then(parsers.parse('the domain name should be {domain:S}'))
def domain_name_should_be(session_browser, domain):
    assert _get_domain_name(session_browser) == domain


@then(parsers.parse('the home page should be {app_name:w}'))
def home_page_should_be(session_browser, app_name):
    assert _check_home_page_redirect(session_browser, app_name)


def _get_hostname(browser):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_id('id_hostname').value


def _set_hostname(browser, hostname):
    functional.nav_to_module(browser, 'config')
    browser.find_by_id('id_hostname').fill(hostname)
    functional.submit(browser)


def _get_domain_name(browser):
    functional.nav_to_module(browser, 'config')
    return browser.find_by_id('id_domainname').value


def _set_home_page(browser, home_page):
    if 'plinth' not in home_page and 'apache' not in home_page:
        home_page = 'shortcut-' + home_page

    functional.nav_to_module(browser, 'config')
    drop_down = browser.find_by_id('id_homepage')
    drop_down.select(home_page)
    functional.submit(browser)


def _check_home_page_redirect(browser, app_name):
    functional.visit(browser, '/')
    return browser.find_by_xpath(
        "//a[contains(@href, '/plinth/') and @title='FreedomBox']")
