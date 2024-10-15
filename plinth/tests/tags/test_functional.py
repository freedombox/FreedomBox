# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for transmission app.
"""

import pytest
from selenium.webdriver.common.keys import Keys

from plinth.tests import functional

pytestmark = [pytest.mark.tags]


def _is_app_listed(session_browser, app):
    """Assert that the specified app is listed on the page."""
    app_links = session_browser.links.find_by_href(f'/plinth/apps/{app}/')
    assert len(app_links) == 1


@pytest.fixture(autouse=True)
def fixture_bittorrent_tag(session_browser):
    """Click on the BitTorrent tag."""
    bittorrent_tag = '/plinth/apps/?tag=BitTorrent'
    functional.login(session_browser)
    functional.nav_to_module(session_browser, 'transmission')
    with functional.wait_for_page_update(session_browser, timeout=10,
                                         expected_url=bittorrent_tag):
        session_browser.links.find_by_href(bittorrent_tag).click()


def test_bittorrent_tag(session_browser):
    """Test that the BitTorrent tag lists Deluge and Transmission."""
    _is_app_listed(session_browser, 'deluge')
    _is_app_listed(session_browser, 'transmission')


def test_search_for_tag(session_browser):
    """Test that searching for a tag returns the expected apps."""
    search_input = session_browser.driver.find_element_by_id('add-tag-input')
    with functional.wait_for_page_update(
            session_browser, timeout=10,
            expected_url='/plinth/apps/?tag=BitTorrent&tag=File%20sharing'):
        search_input.click()
        search_input.send_keys('file')
        search_input.send_keys(Keys.ENTER)
    for app in ['deluge', 'samba', 'sharing', 'syncthing', 'transmission']:
        _is_app_listed(session_browser, app)


def test_click_on_tag(session_browser):
    """Test that clicking on a tag lists the expected apps."""
    search_input = session_browser.driver.find_element_by_id('add-tag-input')
    with functional.wait_for_page_update(
            session_browser, timeout=10,
            expected_url='/plinth/apps/?tag=BitTorrent&tag=File%20sync'):
        search_input.click()
        session_browser.find_by_css(
            ".dropdown-item[data-value='File sync']").click()
    for app in ['deluge', 'nextcloud', 'syncthing', 'transmission']:
        _is_app_listed(session_browser, app)
