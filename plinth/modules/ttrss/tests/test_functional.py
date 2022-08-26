# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ttrss app.
"""

import pytest

from plinth.tests import functional

APP_ID = 'ttrss'

pytestmark = [pytest.mark.apps, pytest.mark.ttrss, pytest.mark.sso]


class TestTTRSSApp(functional.BaseAppTests):
    """Class to customize basic app tests for TTRSS."""

    app_name = 'ttrss'
    has_service = True
    has_web = True

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of app data."""
        functional.app_enable(session_browser, APP_ID)
        _subscribe(session_browser)
        functional.backup_create(session_browser, APP_ID, 'test_ttrss')

        _unsubscribe(session_browser)
        functional.backup_restore(session_browser, APP_ID, 'test_ttrss')

        assert functional.service_is_running(session_browser, APP_ID)
        assert _is_subscribed(session_browser)


def _ttrss_load_main_interface(browser):
    """Load the TT-RSS interface."""
    functional.visit(browser, '/tt-rss/')
    overlay = browser.find_by_id('overlay')
    functional.eventually(lambda: not overlay.visible)


def _is_feed_shown(browser, invert=False):
    return browser.is_text_present('Planet Debian') != invert


def _click_main_menu_item(browser, text):
    """Select an item from the main actions menu."""
    browser.find_by_css('.action-chooser').click()
    browser.find_by_text(text).click()


def _subscribe(browser):
    """Subscribe to a feed in TT-RSS."""

    def _already_subscribed_message():
        return browser.is_text_present(
            'You are already subscribed to this feed.')

    _ttrss_load_main_interface(browser)

    _click_main_menu_item(browser, 'Subscribe to feed...')
    browser.find_by_id('feedDlg_feedUrl').fill(
        'https://planet.debian.org/atom.xml')
    browser.find_by_text('Subscribe').click()
    add_dialog = browser.find_by_css('#feedAddDlg')
    functional.eventually(
        lambda: not add_dialog.visible or _already_subscribed_message())
    if _already_subscribed_message():
        browser.find_by_text('Cancel').click()
        functional.eventually(lambda: not add_dialog.visible)


def _unsubscribe(browser):
    """Unsubscribe from a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    expand = browser.find_by_css('span.dijitTreeExpandoClosed')
    if expand:
        expand.first.click()

    browser.find_by_text('Planet Debian').click()
    _click_main_menu_item(browser, 'Unsubscribe')

    prompt = browser.get_alert()
    prompt.accept()

    # Reload as sometimes the feed does not disappear immediately
    _ttrss_load_main_interface(browser)

    assert functional.eventually(_is_feed_shown, [browser, True])


def _is_subscribed(browser):
    """Return whether subscribed to a feed in TT-RSS."""
    _ttrss_load_main_interface(browser)
    return _is_feed_shown(browser)
