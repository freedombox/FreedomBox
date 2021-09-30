# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for openvpn app.
"""

from pytest_bdd import given, scenarios, then

from plinth.tests import functional

scenarios('openvpn.feature')

base_url = functional.config['DEFAULT']['URL']
shortcut_href = '?selected=shortcut-openvpn'


@given('I download openvpn profile', target_fixture='openvpn_profile')
def openvpn_download_profile(session_browser):
    return _download_profile(session_browser)


@then('the openvpn profile should be downloadable')
def openvpn_profile_downloadable(session_browser):
    _download_profile(session_browser)


@then('openvpn app should not be visible on the front page')
def openvpn_app_not_on_front_page(session_browser):
    session_browser.visit(base_url)
    links = session_browser.links.find_by_href(shortcut_href)
    assert len(links) == 0


@then('the openvpn profile downloaded should be same as before')
def openvpn_profile_download_compare(session_browser, openvpn_profile):
    new_profile = _download_profile(session_browser)
    assert openvpn_profile == new_profile


def _download_profile(browser):
    """Return the content of the current user's OpenVPN profile."""
    browser.visit(base_url)
    browser.click_link_by_href(shortcut_href)
    profile_url = f'{base_url}/plinth/apps/openvpn/profile/'
    return functional.download_file(browser, profile_url)
