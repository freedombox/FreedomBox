# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for transmission app.
"""

import os

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.transmission, pytest.mark.sso]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'transmission')
    yield
    functional.app_disable(session_browser, 'transmission')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'transmission')

    functional.app_enable(session_browser, 'transmission')
    assert functional.is_available(session_browser, 'transmission')

    functional.app_disable(session_browser, 'transmission')
    assert not functional.is_available(session_browser, 'transmission')


def test_upload_torrent(session_browser):
    """Test uploading a torrent to Transmission."""
    functional.app_enable(session_browser, 'transmission')
    _remove_all_torrents(session_browser)
    _upload_sample_torrent(session_browser)
    _assert_number_of_torrents(session_browser, 1)


@pytest.mark.backups
def test_backup_restore(session_browser):
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
        torrents = browser.find_by_css('#torrent_list .torrent')
        if not torrents:
            break

        torrents.first.click()
        functional.eventually(browser.is_element_not_present_by_css,
                              args=['#toolbar-remove.disabled'])
        browser.click_link_by_id('toolbar-remove')
        functional.eventually(
            browser.is_element_not_present_by_css,
            args=['#dialog-container[style="display: none;"]'])
        browser.click_link_by_id('dialog_confirm_button')
        functional.eventually(browser.is_element_present_by_css,
                              args=['#toolbar-remove.disabled'])


def _upload_sample_torrent(browser):
    """Upload a sample torrent into transmission."""
    functional.visit(browser, '/transmission')
    file_path = os.path.join(os.path.dirname(__file__), 'data',
                             'sample.torrent')
    browser.click_link_by_id('toolbar-open')
    functional.eventually(browser.is_element_not_present_by_css,
                          args=['#upload-container[style="display: none;"]'])
    browser.attach_file('torrent_files[]', [file_path])
    browser.click_link_by_id('upload_confirm_button')
    functional.eventually(browser.is_element_present_by_css,
                          args=['#torrent_list .torrent'])


def _get_number_of_torrents(browser):
    """Return the number torrents currently in transmission."""
    return len(browser.find_by_css('#torrent_list .torrent'))
