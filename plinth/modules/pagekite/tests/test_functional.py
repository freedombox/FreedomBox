# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for pagekite app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.pagekite]

# TODO Scenario: Enable standard services
# TODO Scenario: Disable standard services
# TODO Scenario: Add custom service
# TODO Scenario: Delete custom service


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'pagekite')
    yield
    functional.app_disable(session_browser, 'pagekite')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'pagekite')

    functional.app_enable(session_browser, 'pagekite')
    assert functional.service_is_running(session_browser, 'pagekite')

    functional.app_disable(session_browser, 'pagekite')
    assert functional.service_is_not_running(session_browser, 'pagekite')


def test_configure(session_browser):
    """Test pagekite configuration."""
    functional.app_enable(session_browser, 'pagekite')
    _configure(session_browser, 'pagekite.example.com', 8080,
               'mykite.example.com', 'mysecret')
    assert ('pagekite.example.com', 8080, 'mykite.example.com',
            'mysecret') == _get_configuration(session_browser)

    # Capitalized kite name should become lower case.
    _configure(session_browser, 'pagekite.example.com', 8080,
               'Mykite.example.com', 'mysecret')
    assert ('pagekite.example.com', 8080, 'mykite.example.com',
            'mysecret') == _get_configuration(session_browser)


def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    functional.app_enable(session_browser, 'pagekite')
    _configure(session_browser, 'beforebackup.example.com', 8081,
               'beforebackup.example.com', 'beforebackupsecret')
    functional.backup_create(session_browser, 'pagekite', 'test_pagekite')

    _configure(session_browser, 'afterbackup.example.com', 8082,
               'afterbackup.example.com', 'afterbackupsecret')
    functional.backup_restore(session_browser, 'pagekite', 'test_pagekite')

    assert functional.service_is_running(session_browser, 'pagekite')
    assert ('beforebackup.example.com', 8081, 'beforebackup.example.com',
            'beforebackupsecret') == _get_configuration(session_browser)


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
