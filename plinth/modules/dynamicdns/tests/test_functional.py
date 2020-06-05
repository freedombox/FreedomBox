# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for dynamicdns app.
"""

from pytest_bdd import given, scenarios, then, when

from plinth.tests import functional

scenarios('dynamicdns.feature')


@given('dynamicdns is configured')
def dynamicdns_configure(session_browser):
    _configure(session_browser)


@when('I change the dynamicdns configuration')
def dynamicdns_change_config(session_browser):
    _change_config(session_browser)


@then('dynamicdns should have the original configuration')
def dynamicdns_has_original_config(session_browser):
    assert _has_original_config(session_browser)


def _configure(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'http://myip.datasystems24.de')
    functional.submit(browser)


def _has_original_config(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    enabled = browser.find_by_id('id_enabled').value
    service_type = browser.find_by_id('id_service_type').value
    server = browser.find_by_id('id_dynamicdns_server').value
    domain = browser.find_by_id('id_dynamicdns_domain').value
    user = browser.find_by_id('id_dynamicdns_user').value
    ipurl = browser.find_by_id('id_dynamicdns_ipurl').value
    if enabled and service_type == 'GnuDIP' and server == 'example.com' \
       and domain == 'freedombox.example.com' and user == 'tester' \
       and ipurl == 'http://myip.datasystems24.de':
        return True
    else:
        return False


def _change_config(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.find_link_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('2.example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox2.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester2')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting2')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'http://myip2.datasystems24.de')
    functional.submit(browser)
