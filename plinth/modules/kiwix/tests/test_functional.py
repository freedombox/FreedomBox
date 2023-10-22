# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Kiwix app.
"""

import pathlib
from time import sleep

import pytest

from plinth.tests import functional

from .test_privileged import ZIM_ID

pytestmark = [pytest.mark.apps, pytest.mark.sso, pytest.mark.kiwix]

_default_url = functional.config['DEFAULT']['url']

_data_dir = pathlib.Path(__file__).parent / 'data'


class TestKiwixApp(functional.BaseAppTests):
    """Basic functional tests for Kiwix app."""

    app_name = 'kiwix'
    has_service = True
    has_web = True

    def test_add_delete_package(self, session_browser):
        """Test adding/deleting content package to the library."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = _data_dir / 'FreedomBox.zim'
        _add_package(session_browser, str(zim_file))
        assert _is_package_listed(session_browser, 'freedombox')
        assert _is_package_available(session_browser, 'FreedomBox')

        _delete_package(session_browser, ZIM_ID)
        assert not _is_package_listed(session_browser, 'freedombox')
        assert not _is_package_available(session_browser, 'FreedomBox')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backing up and restoring."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = _data_dir / 'FreedomBox.zim'
        _add_package(session_browser, str(zim_file))
        functional.backup_create(session_browser, 'kiwix', 'test_kiwix')

        _delete_package(session_browser, ZIM_ID)
        functional.backup_restore(session_browser, 'kiwix', 'test_kiwix')

        assert _is_package_listed(session_browser, 'freedombox')
        assert _is_package_available(session_browser, 'FreedomBox')

    def test_add_invalid_zim_file(self, session_browser):
        """Test handling of invalid zim files."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = _data_dir / 'invalid.zim'
        _add_package(session_browser, str(zim_file))

        assert not _is_package_listed(session_browser, 'invalid')

    def test_anonymous_access(self, session_browser):
        """Test anonymous access to Kiwix library."""
        functional.app_enable(session_browser, 'kiwix')
        functional.logout(session_browser)
        assert functional.eventually(_shortcut_exists, args=[session_browser])
        assert functional.eventually(_is_anonymous_read_allowed,
                                     args=[session_browser])


def _add_package(browser, file_name):
    """Add a package by uploading the ZIM file in kiwix app page."""
    browser.links.find_by_href('/plinth/apps/kiwix/package/add/').first.click()
    browser.attach_file('kiwix-file', file_name)
    functional.submit(browser, form_class='form-kiwix')


def _is_package_available(browser, title) -> bool:
    """Check whether a ZIM file is available in Kiwix web interface."""
    browser.visit(f'{_default_url}/kiwix')
    sleep(1)  # Allow time for the books to appear
    titles = browser.find_by_id('book__title')
    return any(element.value == title for element in titles)


def _is_package_listed(browser, name) -> bool:
    """Return whether a content package is list in kiwix app page."""
    functional.nav_to_module(browser, 'kiwix')
    links_found = browser.links.find_by_partial_href(f'/kiwix/viewer#{name}')
    return len(links_found) == 1


def _delete_package(browser, zim_id):
    """Delete a content package from the kiwix app page."""
    functional.nav_to_module(browser, 'kiwix')
    link = browser.links.find_by_href(
        f'/plinth/apps/kiwix/package/{zim_id}/delete/')
    if not link:
        raise ValueError('ZIM file missing!')

    link.first.click()
    functional.submit(browser, form_class='form-delete')


def _is_anonymous_read_allowed(browser) -> bool:
    """Check if Kiwix library page can be accessed without logging in."""
    functional.visit(browser, '/kiwix')
    return browser.is_element_present_by_id('kiwixfooter')


def _shortcut_exists(browser) -> bool:
    """Check that the Kiwix shortcut exists on the front page."""
    browser.visit(_default_url)
    links_found = browser.links.find_by_href('/kiwix')
    return len(links_found) == 1
