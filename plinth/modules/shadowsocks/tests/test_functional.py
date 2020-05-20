# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for shadowsocks app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('shadowsocks.feature')


@given('the shadowsocks application is configured')
def configure_shadowsocks(session_browser):
    _configure(session_browser, 'example.com', 'fakepassword')


@when(
    parsers.parse('I configure shadowsocks with server {server:S} and '
                  'password {password:w}'))
def configure_shadowsocks_with_details(session_browser, server, password):
    _configure(session_browser, server, password)


@then(
    parsers.parse('shadowsocks should be configured with server {server:S} '
                  'and password {password:w}'))
def assert_shadowsocks_configuration(session_browser, server, password):
    assert (server, password) == _get_configuration(session_browser)


def _configure(browser, server, password):
    """Configure shadowsocks client with given server details."""
    functional.visit(browser, '/plinth/apps/shadowsocks/')
    browser.find_by_id('id_server').fill(server)
    browser.find_by_id('id_password').fill(password)
    functional.submit(browser, form_class='form-configuration')


def _get_configuration(browser):
    """Return the server and password currently configured in shadowsocks."""
    functional.visit(browser, '/plinth/apps/shadowsocks/')
    server = browser.find_by_id('id_server').value
    password = browser.find_by_id('id_password').value
    return server, password
