# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for shadowsocks app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.shadowsocks]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'shadowsocks')
    _configure(session_browser, 'example.com', 'fakepassword')
    yield
    functional.app_disable(session_browser, 'shadowsocks')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'shadowsocks')

    functional.app_enable(session_browser, 'shadowsocks')
    assert functional.service_is_running(session_browser, 'shadowsocks')

    functional.app_disable(session_browser, 'shadowsocks')
    assert functional.service_is_not_running(session_browser, 'shadowsocks')


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    functional.app_enable(session_browser, 'shadowsocks')
    _configure(session_browser, 'example.com', 'beforebackup123')
    functional.backup_create(session_browser, 'shadowsocks',
                             'test_shadowsocks')

    _configure(session_browser, 'example.org', 'afterbackup123')
    functional.backup_restore(session_browser, 'shadowsocks',
                              'test_shadowsocks')

    assert functional.service_is_running(session_browser, 'shadowsocks')
    assert _get_configuration(session_browser) == ('example.com',
                                                   'beforebackup123')


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
