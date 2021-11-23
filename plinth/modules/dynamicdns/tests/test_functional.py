# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for dynamicdns app.
"""

import time

import pytest

from plinth.tests import functional

pytestmark = [
    pytest.mark.system, pytest.mark.essential, pytest.mark.dynamicdns
]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_capitalized_domain_name(session_browser):
    """Test handling of capitalized domain name."""
    _configure(session_browser)
    _configure_domain(session_browser, 'FreedomBox.example.com')
    assert _get_domain(session_browser) == 'freedombox.example.com'


def test_backup_and_restore(session_browser):
    """Test backup and restore of configuration."""
    _configure(session_browser)
    functional.backup_create(session_browser, 'dynamicdns', 'test_dynamicdns')

    _change_config(session_browser)
    functional.backup_restore(session_browser, 'dynamicdns', 'test_dynamicdns')

    assert _has_original_config(session_browser)


# TODO Scenario: Configure GnuDIP service
# TODO Scenario: Configure noip.com service
# TODO Scenario: Configure selfhost.bz service
# TODO Scenario: Configure freedns.afraid.org service
# TODO Scenario: Configure other update URL service


def _configure(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.links.find_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'https://ddns.freedombox.org/ip/')
    functional.submit(browser)

    # After a domain name change, Let's Encrypt will restart the web
    # server and could cause a connection failure.
    time.sleep(1)
    functional.eventually(functional.nav_to_module, [browser, 'dynamicdns'])


def _has_original_config(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.links.find_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    enabled = browser.find_by_id('id_enabled').value
    service_type = browser.find_by_id('id_service_type').value
    server = browser.find_by_id('id_dynamicdns_server').value
    domain = browser.find_by_id('id_dynamicdns_domain').value
    user = browser.find_by_id('id_dynamicdns_user').value
    ipurl = browser.find_by_id('id_dynamicdns_ipurl').value
    if enabled and service_type == 'GnuDIP' and server == 'example.com' \
       and domain == 'freedombox.example.com' and user == 'tester' \
       and ipurl == 'https://ddns.freedombox.org/ip/':
        return True
    else:
        return False


def _change_config(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.links.find_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_enabled').check()
    browser.find_by_id('id_service_type').select('GnuDIP')
    browser.find_by_id('id_dynamicdns_server').fill('2.example.com')
    browser.find_by_id('id_dynamicdns_domain').fill('freedombox2.example.com')
    browser.find_by_id('id_dynamicdns_user').fill('tester2')
    browser.find_by_id('id_dynamicdns_secret').fill('testingtesting2')
    browser.find_by_id('id_dynamicdns_ipurl').fill(
        'https://ddns2.freedombox.org/ip/')
    functional.submit(browser)

    # After a domain name change, Let's Encrypt will restart the web
    # server and could cause a connection failure.
    time.sleep(1)
    functional.eventually(functional.nav_to_module, [browser, 'dynamicdns'])


def _configure_domain(browser, domain):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.links.find_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    browser.find_by_id('id_dynamicdns_domain').fill(domain)
    functional.submit(browser)

    # After a domain name change, Let's Encrypt will restart the web
    # server and could cause a connection failure.
    time.sleep(1)
    functional.eventually(functional.nav_to_module, [browser, 'dynamicdns'])


def _get_domain(browser):
    functional.nav_to_module(browser, 'dynamicdns')
    browser.links.find_by_href(
        '/plinth/sys/dynamicdns/configure/').first.click()
    return browser.find_by_id('id_dynamicdns_domain').value
