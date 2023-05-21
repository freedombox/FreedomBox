# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Shadowsocks Client app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.shadowsocks]


class TestShadowsocksApp(functional.BaseAppTests):
    app_name = 'shadowsocks'
    has_service = True
    has_web = False

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.install(session_browser, 'shadowsocks')
        _configure(session_browser, 'example.com', 'fakepassword')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of configuration."""
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
