# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for pagekite app.
"""

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('pagekite.feature')


@when(
    parsers.parse('I configure pagekite with host {host:S}, port {port:d}, '
                  'kite name {kite_name:S} and kite secret {kite_secret:w}'))
def pagekite_configure(session_browser, host, port, kite_name, kite_secret):
    _configure(session_browser, host, port, kite_name, kite_secret)


@then(
    parsers.parse(
        'pagekite should be configured with host {host:S}, port {port:d}, '
        'kite name {kite_name:S} and kite secret {kite_secret:w}'))
def pagekite_assert_configured(session_browser, host, port, kite_name,
                               kite_secret):
    assert (host, port, kite_name,
            kite_secret) == _get_configuration(session_browser)


def _configure(browser, host, port, kite_name, kite_secret):
    """Configure pagekite basic parameters."""
    functional.nav_to_module(browser, 'pagekite')
    # time.sleep(0.250)  # Wait for 200ms show animation to complete
    browser.fill('pagekite-server_domain', host)
    browser.fill('pagekite-server_port', str(port))
    browser.fill('pagekite-kite_name', kite_name)
    browser.fill('pagekite-kite_secret', kite_secret)
    functional.submit(browser, form_class='form-configuration')


def _get_configuration(browser):
    """Return pagekite basic parameters."""
    functional.nav_to_module(browser, 'pagekite')
    return (browser.find_by_name('pagekite-server_domain').value,
            int(browser.find_by_name('pagekite-server_port').value),
            browser.find_by_name('pagekite-kite_name').value,
            browser.find_by_name('pagekite-kite_secret').value)
