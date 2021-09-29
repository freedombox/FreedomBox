# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for openvpn app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.openvpn]

base_url = functional.config['DEFAULT']['URL']
shortcut_href = '?selected=shortcut-openvpn'


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'openvpn')
    yield
    functional.app_disable(session_browser, 'openvpn')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'openvpn')

    functional.app_enable(session_browser, 'openvpn')
    assert functional.service_is_running(session_browser, 'openvpn')

    functional.app_disable(session_browser, 'openvpn')
    assert functional.service_is_not_running(session_browser, 'openvpn')


def test_download_profile(session_browser):
    """Test that OpenVPN profile is downloadable."""
    functional.app_enable(session_browser, 'openvpn')
    _download_profile(session_browser)


def test_user_group(session_browser):
    """Test that only users in vpn group have access."""
    functional.app_enable(session_browser, 'openvpn')
    if not functional.user_exists(session_browser, 'vpnuser'):
        functional.create_user(session_browser, 'vpnuser', groups=['vpn'])
    if not functional.user_exists(session_browser, 'nonvpnuser'):
        functional.create_user(session_browser, 'nonvpnuser', groups=[])

    functional.login_with_account(session_browser, base_url, 'vpnuser')
    _download_profile(session_browser)

    functional.login_with_account(session_browser, base_url, 'nonvpnuser')
    _not_on_front_page(session_browser)

    functional.login(session_browser)


def test_backup_restore(session_browser):
    """Test backup and restore of app data."""
    functional.app_enable(session_browser, 'openvpn')
    profile = _download_profile(session_browser)
    functional.backup_create(session_browser, 'openvpn', 'test_openvpn')

    functional.backup_restore(session_browser, 'openvpn', 'test_openvpn')
    _profile_download_compare(session_browser, profile)


def _not_on_front_page(session_browser):
    session_browser.visit(base_url)
    links = session_browser.links.find_by_href(shortcut_href)
    assert len(links) == 0


def _profile_download_compare(session_browser, openvpn_profile):
    new_profile = _download_profile(session_browser)
    assert openvpn_profile == new_profile


def _download_profile(browser):
    """Return the content of the current user's OpenVPN profile."""
    browser.visit(base_url)
    browser.click_link_by_href(shortcut_href)
    profile_url = f'{base_url}/plinth/apps/openvpn/profile/'
    return functional.download_file(browser, profile_url)
