# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for openvpn app.
"""

from pytest_bdd import given, scenarios, then

from plinth.tests import functional

scenarios('openvpn.feature')


@given('I download openvpn profile')
def openvpn_download_profile(session_browser):
    return _download_profile(session_browser)


@then('the openvpn profile should be downloadable')
def openvpn_profile_downloadable(session_browser):
    _download_profile(session_browser)


@then('the openvpn profile downloaded should be same as before')
def openvpn_profile_download_compare(session_browser,
                                     openvpn_download_profile):
    new_profile = _download_profile(session_browser)
    assert openvpn_download_profile == new_profile


def _download_profile(browser):
    """Return the content of the current user's OpenVPN profile."""
    default_url = functional.config['DEFAULT']['URL']
    browser.visit(default_url)
    browser.click_link_by_href('?selected=shortcut-openvpn')
    return functional.download_file(
        browser, f'{default_url}/plinth/apps/openvpn/profile/')
