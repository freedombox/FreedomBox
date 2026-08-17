# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for deluge app.
"""

import os
import time

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.deluge]


class TestDelugeApp(functional.BaseAppTests):
    app_name = 'deluge'
    has_service = True
    has_web = True

    def test_bittorrent_group(self, session_browser):
        """Test if only users in bit-torrent group can access Deluge."""
        functional.app_enable(session_browser, 'deluge')
        if not functional.user_exists(session_browser, 'delugeuser'):
            functional.create_user(session_browser, 'delugeuser',
                                   groups=['bit-torrent'])

        if not functional.user_exists(session_browser, 'nogroupuser'):
            functional.create_user(session_browser, 'nogroupuser')

        functional.login_with_account(session_browser, functional.base_url,
                                      'delugeuser')
        assert functional.is_available(session_browser, 'deluge')

        functional.login_with_account(session_browser, functional.base_url,
                                      'nogroupuser')
        assert not functional.is_available(session_browser, 'deluge')

    def test_upload_torrent(self, session_browser):
        """Test uploading a torrent."""
        functional.app_enable(session_browser, 'deluge')
        _remove_all_torrents(session_browser)
        _upload_sample_torrent(session_browser)
        assert len(_get_torrents(session_browser)) == 1

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore."""
        functional.app_enable(session_browser, 'deluge')
        _remove_all_torrents(session_browser)
        _upload_sample_torrent(session_browser)
        functional.backup_create(session_browser, 'deluge', 'test_deluge')

        _remove_all_torrents(session_browser)
        functional.backup_restore(session_browser, 'deluge', 'test_deluge')
        assert functional.service_is_running(session_browser, 'deluge')
        assert len(_get_torrents(session_browser)) == 1


def _get_active_window_title(browser):
    """Return the title of the currently active window in Deluge."""
    return browser.evaluate_script(
        'Ext.WindowMgr.getActive() ? Ext.WindowMgr.getActive().title : null')


def _ensure_logged_in(browser):
    """Ensure that password dialog is answered and we can interact."""
    url = functional.base_url + '/deluge'

    def service_is_available():
        if browser.is_element_present_by_xpath(
                '//h1[text()="Service Unavailable"]'):
            functional.access_url(browser, 'deluge')
            return False

        return True

    if browser.url != url:
        browser.visit(url)
        # After a backup restore, service may not be available immediately
        functional.eventually(service_is_available)

    functional.eventually(browser.is_element_present_by_id, ['add'])

    def logged_in():
        active_window_title = _get_active_window_title(browser)
        # Change Default Password window appears once.
        if active_window_title == 'Change Default Password':
            _click_active_window_button(browser, 'No')

        if active_window_title == 'Login':
            browser.find_by_id('_password').first.fill('deluge')
            _click_active_window_button(browser, 'Login')

        return browser.is_element_present_by_css(
            '.x-deluge-statusbar.x-connected')

    functional.eventually(logged_in)


def _remove_all_torrents(browser):
    """Remove all torrents from deluge."""
    _ensure_logged_in(browser)

    for torrent in _get_torrents(browser):
        torrent.click()
        # Click remove toolbar button
        browser.find_by_id('remove').first.click()

        # Remove window shows up
        assert functional.eventually(
            lambda: _get_active_window_title(browser) == 'Remove Torrent')

        _click_active_window_button(browser, 'Remove With Data')

        # Remove window disappears
        assert functional.eventually(
            lambda: not _get_active_window_title(browser))


def _get_active_window_id(browser):
    """Return the ID of the currently active window."""
    return browser.evaluate_script('Ext.WindowMgr.getActive().id')


def _click_active_window_button(browser, button_text):
    """Click an action button in the active window."""
    browser.execute_script('''
        active_window = Ext.WindowMgr.getActive();
        active_window.buttons.forEach(function (button) {{
            if (button.text == "{button_text}")
                button.btnEl.dom.click()
        }})'''.format(button_text=button_text))


def _upload_sample_torrent(browser):
    """Upload a sample torrent into deluge."""
    _ensure_logged_in(browser)

    number_of_torrents = len(_get_torrents(browser))

    # Click add toolbar button
    browser.find_by_id('add').first.click()

    # Add window appears
    functional.eventually(
        lambda: _get_active_window_title(browser) == 'Add Torrents')

    file_path = os.path.join(os.path.dirname(__file__), 'data',
                             'sample.torrent')
    browser.attach_file('file', file_path)

    # Click Add
    time.sleep(1)
    _click_active_window_button(browser, 'Add')

    functional.eventually(
        lambda: len(_get_torrents(browser)) > number_of_torrents)


def _get_torrents(browser):
    """Return list of torrents currently in deluge."""
    _ensure_logged_in(browser)
    # wait until torrent list is loaded
    functional.eventually(browser.is_element_present_by_css, ['.x-deluge-all'])

    return browser.find_by_css('#torrentGrid .torrent-name')
