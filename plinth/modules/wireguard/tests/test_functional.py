# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for wireguard app.
"""

import urllib

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.wireguard]


class TestWireguardApp(functional.BaseAppTests):
    app_name = 'wireguard'
    has_web = False

    _client_public_key1 = '8dlHfuAsU0WsnpQkNd8fguwmBtFX5/CkO0xYKbNBt24='
    _client_public_key2 = 'xM/vyXbYtMf9bDTZY3W2x7Moxw4m1ckpnZvVSd4DLho='

    _server = [
        {
            'peer_endpoint': 'wg1.example.org:1234',
            'peer_public_key': 'HBCqZk4B93N6q19zNleJkAVs+PEfWAPgPpKnrhL/CVw=',
            'ip_address': '10.0.0.2',
            'private_key': '',
            'preshared_key': ''
        },
        {
            'peer_endpoint': 'wg2.example.org:5678',
            'peer_public_key': 'Z/iHo0vaeSN8Ykk5KwhQ819MMU5nyzD7y7xFFthlxXI=',
            'ip_address': '192.168.0.2',
            'private_key': 'QC2xEZMn3bgNsSVFrU51+ALSUiUaWg6gRWigh3EeVm0=',
            'preshared_key': 'AHxZ4Rr8Ij4L1aq+ceusSIgBfluqiI9Vb5I2UtQFanI='
        },
    ]

    def test_backup_restore(self, session_browser):
        """Skip the test."""
        pytest.skip('Does not implement backup/restore.')

    @staticmethod
    def _get_client_href(key):
        """Return the href for client show page."""
        key = urllib.parse.quote(urllib.parse.quote(key, safe=''))
        return f'/plinth/apps/wireguard/client/{key}/show/'

    def _client_exists(self, browser, key):
        """Check whether a client key exists."""
        functional.nav_to_module(browser, 'wireguard')
        href = browser.links.find_by_href(self._get_client_href(key))
        return bool(href)

    def _assert_client_details(self, browser, key):
        """Check that the client's details are correct."""

        def get_value(key):
            return browser.find_by_css(f'tr.{key} > td').first.text

        functional.nav_to_module(browser, 'wireguard')
        href = browser.links.find_by_href(self._get_client_href(key))
        href.first.click()
        assert get_value('client-public-key') == key

    @staticmethod
    def _add_client(browser, key):
        """Add a client."""
        functional.nav_to_module(browser, 'wireguard')
        # Start the server on FreedomBox, if needed.
        start_server_button = browser.find_by_css('.btn-start-server')
        if start_server_button:
            start_server_button.first.click()

        browser.find_by_css('.btn-add-client').first.click()
        browser.find_by_id('id_public_key').fill(key)
        functional.submit(browser, form_class='form-add-client')

    def _edit_client(self, browser, key1, key2):
        """Edit a client"""
        functional.nav_to_module(browser, 'wireguard')
        browser.links.find_by_href(self._get_client_href(key1)).first.click()
        browser.find_by_css('.btn-edit-client').first.click()
        browser.find_by_id('id_public_key').fill(key2)
        functional.submit(browser, form_class='form-edit-client')

    def _delete_client(self, browser, key):
        """Delete a client"""
        functional.nav_to_module(browser, 'wireguard')
        browser.links.find_by_href(self._get_client_href(key)).first.click()
        browser.find_by_css('.btn-delete-client').first.click()
        functional.submit(browser, form_class='form-delete-client')

    def test_add_edit_delete_client(self, session_browser):
        """Test adding, editing and deleting a WireGuard client."""
        if self._client_exists(session_browser, self._client_public_key1):
            self._delete_client(session_browser, self._client_public_key1)

        if self._client_exists(session_browser, self._client_public_key2):
            self._delete_client(session_browser, self._client_public_key2)

        self._add_client(session_browser, self._client_public_key1)
        assert self._client_exists(session_browser, self._client_public_key1)

        self._edit_client(session_browser, self._client_public_key1,
                          self._client_public_key2)
        assert not self._client_exists(session_browser,
                                       self._client_public_key1)
        assert self._client_exists(session_browser, self._client_public_key2)

        self._delete_client(session_browser, self._client_public_key2)
        assert not self._client_exists(session_browser,
                                       self._client_public_key2)

    @staticmethod
    def _get_server_href(browser, key):
        """Return the href for server show page."""
        return browser.find_by_css(
            f'.peer-public-key[data-public-key="{key}"] a')

    def _server_exists(self, browser, config):
        """Check whether a server key exists."""
        functional.nav_to_module(browser, 'wireguard')
        href = self._get_server_href(browser, config['peer_public_key'])
        return bool(href)

    def _assert_server_details(self, browser, config):
        """Check that the server's details are correct."""

        def get_value(key):
            return browser.find_by_css(f'tr.{key} > td').first.text

        functional.nav_to_module(browser, 'wireguard')
        href = self._get_server_href(browser, config['peer_public_key'])
        href.first.click()
        assert get_value('peer-endpoint') == config['peer_endpoint']
        assert get_value('peer-public-key') == config['peer_public_key']
        assert get_value('server-ip-address') == config['ip_address']
        assert get_value('peer-preshared-key') == (config['preshared_key']
                                                   or 'None')

    @staticmethod
    def _add_server(browser, config):
        """Add a server."""
        functional.nav_to_module(browser, 'wireguard')
        browser.find_by_css('.btn-add-server').first.click()
        browser.find_by_id('id_peer_endpoint').fill(config['peer_endpoint'])
        browser.find_by_id('id_peer_public_key').fill(
            config['peer_public_key'])
        browser.find_by_id('id_ip_address').fill(config['ip_address'])
        browser.find_by_id('id_private_key').fill(config['private_key'])
        browser.find_by_id('id_preshared_key').fill(config['preshared_key'])
        functional.submit(browser, form_class='form-add-server')

    def _edit_server(self, browser, config1, config2):
        """Edit a server."""
        functional.nav_to_module(browser, 'wireguard')
        self._get_server_href(browser,
                              config1['peer_public_key']).first.click()
        browser.find_by_css('.btn-edit-server').first.click()
        browser.find_by_id('id_peer_endpoint').fill(config2['peer_endpoint'])
        browser.find_by_id('id_peer_public_key').fill(
            config2['peer_public_key'])
        browser.find_by_id('id_ip_address').fill(config2['ip_address'])
        browser.find_by_id('id_private_key').fill(config2['private_key'])
        browser.find_by_id('id_preshared_key').fill(config2['preshared_key'])
        functional.submit(browser, form_class='form-edit-server')

    def _delete_server(self, browser, config):
        """Delete a server"""
        functional.nav_to_module(browser, 'wireguard')
        self._get_server_href(browser, config['peer_public_key']).first.click()
        browser.find_by_css('.btn-delete-server').first.click()
        functional.submit(browser, form_class='form-delete-server')

    def test_add_edit_delete_server(self, session_browser):
        """Test adding, editing and deleting a WireGuard server."""
        if self._server_exists(session_browser, self._server[0]):
            self._delete_server(session_browser, self._server[0])

        if self._server_exists(session_browser, self._server[1]):
            self._delete_server(session_browser, self._server[1])

        self._add_server(session_browser, self._server[0])
        self._assert_server_details(session_browser, self._server[0])

        # XXX: Editing the connection is very flaky. Fails, incorrect and
        # crashes. Fix it.

        # self._edit_server(session_browser, self._server[0],
        # self._server[1]) assert not self._server_exists(session_browser,
        # self._server[0]) self._assert_server_details(session_browser,
        # self._server[1])

        # self._delete_server(session_browser, self._server[1])
        # assert not self._server_exists(session_browser, self._server[1])

        self._delete_server(session_browser, self._server[0])
        assert not self._server_exists(session_browser, self._server[0])
