# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for transmission app.
"""

import os

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('transmission.feature')


@when('all torrents are removed from transmission')
def transmission_remove_all_torrents(session_browser):
    _remove_all_torrents(session_browser)


@when('I upload a sample torrent to transmission')
def transmission_upload_sample_torrent(session_browser):
    _upload_sample_torrent(session_browser)


@then(
    parsers.parse(
        'there should be {torrents_number:d} torrents listed in transmission'))
def transmission_assert_number_of_torrents(session_browser, torrents_number):
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
