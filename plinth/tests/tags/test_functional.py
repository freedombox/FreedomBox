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


@pytest.fixture(name='bittorrent_tag')
def fixture_bittorrent_tag(session_browser):
    """Click on the BitTorrent tag."""
    bittorrent_tag = '/plinth/apps/?tag=BitTorrent'
    functional.login(session_browser)
    functional.nav_to_module(session_browser, 'transmission')
    with functional.wait_for_page_update(session_browser, timeout=10,
                                         expected_url=bittorrent_tag):
        session_browser.links.find_by_href(bittorrent_tag).click()


@pytest.fixture(name='locale')
def fixture_locale(session_browser):
    """Set a different language for a user."""
    functional.login(session_browser)
    try:
        functional.user_set_language(session_browser, 'es')
        yield
    finally:
        functional.user_set_language(session_browser, '')


def test_bittorrent_tag(session_browser, bittorrent_tag):
    """Test that the BitTorrent tag lists Deluge and Transmission."""
    _is_app_listed(session_browser, 'deluge')
    _is_app_listed(session_browser, 'transmission')


def test_search_for_tag(session_browser, bittorrent_tag):
    """Test that searching for a tag returns the expected apps."""
    search_input = session_browser.find_by_id('add-tag-input').first
    with functional.wait_for_page_update(
            session_browser, timeout=10,
            expected_url='/plinth/apps/?tag=BitTorrent&tag=File+sharing'):
        search_input.click()
        search_input.type('file sharing')
        search_input.type(Keys.ENTER)

    for app in ['deluge', 'samba', 'sharing', 'syncthing', 'transmission']:
        _is_app_listed(session_browser, app)


def test_click_on_tag(session_browser, bittorrent_tag):
    """Test that clicking on a tag lists the expected apps."""
    search_input = session_browser.find_by_id('add-tag-input').first
    with functional.wait_for_page_update(
            session_browser, timeout=10,
            expected_url='/plinth/apps/?tag=BitTorrent&tag=File+sync'):
        search_input.click()
        session_browser.find_by_css(
            ".dropdown-item[data-tag='File sync']").click()

    for app in ['deluge', 'nextcloud', 'syncthing', 'transmission']:
        _is_app_listed(session_browser, app)


def test_tag_localization(session_browser, locale):
    """Test that tags are localized and tests in done localized."""
    functional.visit(session_browser, '/plinth/apps/?tag=Sharing')
    badge = session_browser.find_by_css('.tag-badge[data-tag="Sharing"]').first
    assert 'Compartir' in badge.text

    search_input = session_browser.find_by_id('add-tag-input').first
    with functional.wait_for_page_update(
            session_browser, timeout=10,
            expected_url='/plinth/apps/?tag=Sharing&tag=Bookmarks'):
        search_input.click()
        search_input.type('Marcadores')
        search_input.type(Keys.ENTER)
