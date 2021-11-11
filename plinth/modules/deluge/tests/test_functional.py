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

        functional.login(session_browser)

    def test_upload_torrent(self, session_browser):
        """Test uploading a torrent."""
        functional.app_enable(session_browser, 'deluge')
        _remove_all_torrents(session_browser)
        _upload_sample_torrent(session_browser)
        assert _get_number_of_torrents(session_browser) == 1

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
        assert _get_number_of_torrents(session_browser) == 1


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

        time.sleep(1)  # Wait for Ext.js application in initialize

    if _get_active_window_title(browser) != 'Login':
        return

    browser.find_by_id('_password').first.fill('deluge')
    _click_active_window_button(browser, 'Login')

    assert functional.eventually(
        lambda: _get_active_window_title(browser) != 'Login')
    functional.eventually(browser.is_element_not_present_by_css,
                          args=['#add.x-item-disabled'], timeout=0.3)


def _open_connection_manager(browser):
    """Open the connection manager dialog if not already open."""
    title = 'Connection Manager'
    if _get_active_window_title(browser) == title:
        return

    browser.find_by_css('button.x-deluge-connection-manager').first.click()
    functional.eventually(lambda: _get_active_window_title(browser) == title)


def _ensure_connected(browser):
    """Type the connection password if required and start Deluge daemon."""
    _ensure_logged_in(browser)

    # Change Default Password window appears once.
    if _get_active_window_title(browser) == 'Change Default Password':
        _click_active_window_button(browser, 'No')

    assert functional.eventually(browser.is_element_not_present_by_css,
                                 args=['#add.x-item-disabled'])


def _remove_all_torrents(browser):
    """Remove all torrents from deluge."""
    _ensure_connected(browser)

    while browser.find_by_css('#torrentGrid .torrent-name'):
        browser.find_by_css('#torrentGrid .torrent-name').first.click()

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
    _ensure_connected(browser)

    number_of_torrents = _get_number_of_torrents(browser)

    # Click add toolbar button
    browser.find_by_id('add').first.click()

    # Add window appears
    functional.eventually(
        lambda: _get_active_window_title(browser) == 'Add Torrents')

    file_path = os.path.join(os.path.dirname(__file__), 'data',
                             'sample.torrent')

    if browser.find_by_id('fileUploadForm'):  # deluge-web 2.x
        browser.attach_file('file', file_path)
    else:  # deluge-web 1.x
        browser.find_by_css('button.x-deluge-add-file').first.click()

        # Add from file window appears
        functional.eventually(
            lambda: _get_active_window_title(browser) == 'Add from File')

        # Attach file
        browser.attach_file('file', file_path)

        # Click Add
        _click_active_window_button(browser, 'Add')

        functional.eventually(
            lambda: _get_active_window_title(browser) == 'Add Torrents')

    # Click Add
    time.sleep(1)
    _click_active_window_button(browser, 'Add')

    functional.eventually(
        lambda: _get_number_of_torrents(browser) > number_of_torrents)


def _get_number_of_torrents(browser):
    """Return the number torrents currently in deluge."""
    _ensure_connected(browser)

    return len(browser.find_by_css('#torrentGrid .torrent-name'))
