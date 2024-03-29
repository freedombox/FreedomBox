# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Shadowsocks Server app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.shadowsocksserver]


class TestShadowsocksServerApp(functional.BaseAppTests):
    app_name = 'shadowsocksserver'
    has_service = True
    has_web = False

    def install_and_setup(self, session_browser):
        """Install the app and run setup."""
        super().install_and_setup(session_browser)
        _configure(session_browser, 'fakepassword')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of configuration."""
        _configure(session_browser, 'beforebackup123')
        functional.backup_create(session_browser, 'shadowsocksserver',
                                 'test_shadowsocksserver')

        _configure(session_browser, 'afterbackup123')
        functional.backup_restore(session_browser, 'shadowsocksserver',
                                  'test_shadowsocksserver')

        assert functional.service_is_running(session_browser,
                                             'shadowsocksserver')
        assert _get_configuration(session_browser) == 'beforebackup123'


def _configure(browser, password):
    """Configure Shadowsocks Server with given details."""
    functional.visit(browser, '/plinth/apps/shadowsocksserver/')
    browser.find_by_id('id_password').fill(password)
    functional.submit(browser, form_class='form-configuration')


def _get_configuration(browser):
    """Return the password currently configured in Shadowsocks Server."""
    functional.visit(browser, '/plinth/apps/shadowsocksserver/')
    password = browser.find_by_id('id_password').value
    return password
