# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for transmission app.
"""

import os

import pytest
from splinter.exceptions import ElementDoesNotExist

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.transmission, pytest.mark.sso]


class TestTransmissionApp(functional.BaseAppTests):
    app_name = 'transmission'
    has_service = False
    has_web = True

    def test_upload_torrent(self, session_browser):
        """Test uploading a torrent to Transmission."""
        functional.app_enable(session_browser, 'transmission')
        _remove_all_torrents(session_browser)
        _upload_sample_torrent(session_browser)
        _assert_number_of_torrents(session_browser, 1)

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of app data."""
        functional.app_enable(session_browser, 'transmission')
        _remove_all_torrents(session_browser)
        _upload_sample_torrent(session_browser)
        functional.backup_create(session_browser, 'transmission',
                                 'test_transmission')

        _remove_all_torrents(session_browser)
        functional.backup_restore(session_browser, 'transmission',
                                  'test_transmission')

        assert functional.service_is_running(session_browser, 'transmission')
        _assert_number_of_torrents(session_browser, 1)


def _assert_number_of_torrents(session_browser, torrents_number):
    functional.visit(session_browser, '/transmission')
    assert functional.eventually(
        lambda: torrents_number == _get_number_of_torrents(session_browser))


def _remove_all_torrents(browser):
    """Remove all torrents from transmission."""
    functional.visit(browser, '/transmission')
    while True:
        torrents = browser.find_by_css(
            '#torrent_list .torrent, #torrent-list .torrent')
        if not torrents:
            break

        torrents.first.click()
        functional.eventually(
            browser.is_element_not_present_by_css,
            args=['#toolbar-remove.disabled,#toolbar-delete.disabled'])
        browser.find_by_css('#toolbar-remove,#toolbar-delete').first.click()
        functional.eventually(
            browser.is_element_not_present_by_css,
            args=['#dialog-container[style="display: none;"]'])
        try:
            browser.find_by_id('dialog_confirm_button').click()
        except ElementDoesNotExist:
            browser.find_by_css('.dialog-window button').last.click()

        functional.eventually(browser.is_element_present_by_css,
                              args=['#toolbar-remove.disabled'])


def _upload_sample_torrent(browser):
    """Upload a sample torrent into transmission."""
    functional.visit(browser, '/transmission')
    file_path = os.path.join(os.path.dirname(__file__), 'data',
                             'sample.torrent')
    browser.find_by_id('toolbar-open').click()
    # check if older version of Transmission in Debian Bookworm
    transmission_old = browser.is_element_present_by_id('transmission_body')
    if transmission_old:
        functional.eventually(
            browser.is_element_not_present_by_css,
            args=['#upload_container[style="display: none;"]'])
        browser.attach_file('torrent_files[]', [file_path])
        browser.find_by_id('upload_confirm_button').click()
        functional.eventually(browser.is_element_present_by_css,
                              args=['#torrent_list .torrent'])
    else:
        functional.eventually(browser.is_element_present_by_tag,
                              args=['dialog'])
        browser.attach_file('torrent-files[]', [file_path])
        browser.find_by_css('.dialog-window button').last.click()
        functional.eventually(browser.is_element_present_by_css,
                              args=['#torrent-list .torrent'])


def _get_number_of_torrents(browser):
    """Return the number torrents currently in transmission."""
    return len(
        browser.find_by_css('#torrent_list .torrent, #torrent-list .torrent'))
