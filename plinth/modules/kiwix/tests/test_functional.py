# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Kiwix app.
"""

import pkg_resources
import pytest

from time import sleep
from plinth.modules.kiwix.tests.test_privileged import ZIM_ID

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.sso, pytest.mark.kiwix]

_default_url = functional.config['DEFAULT']['url']

ZIM_ID = 'bc4f8cdf-5626-2b13-3860-0033deddfbea'


class TestKiwixApp(functional.BaseAppTests):
    app_name = 'kiwix'
    has_service = True
    has_web = True

    def test_add_delete_content_package(self, session_browser):
        """Test adding/deleting content package to the library."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = pkg_resources.resource_filename(
            'plinth.modules.kiwix.tests', 'data/FreedomBox.zim')
        _add_content_package(session_browser, zim_file)
        assert _is_content_package_listed(session_browser, 'freedombox')
        assert _is_content_package_available(session_browser, 'FreedomBox')

        _delete_content_package(session_browser, ZIM_ID)
        assert not _is_content_package_listed(session_browser, 'freedombox')
        assert not _is_content_package_available(session_browser, 'FreedomBox')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backing up and restoring."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = pkg_resources.resource_filename(
            'plinth.modules.kiwix.tests', 'data/FreedomBox.zim')
        _add_content_package(session_browser, zim_file)
        functional.backup_create(session_browser, 'kiwix', 'test_kiwix')

        _delete_content_package(session_browser, ZIM_ID)
        functional.backup_restore(session_browser, 'kiwix', 'test_kiwix')

        assert _is_content_package_listed(session_browser, 'freedombox')
        assert _is_content_package_available(session_browser, 'FreedomBox')

    def test_add_invalid_zim_file(self, session_browser):
        """Test handling of invalid zim files."""
        functional.app_enable(session_browser, 'kiwix')

        zim_file = pkg_resources.resource_filename(
            'plinth.modules.kiwix.tests', 'data/invalid.zim')
        _add_content_package(session_browser, zim_file)

        assert not _is_content_package_listed(session_browser, 'invalid')


def _add_content_package(browser, file_name):
    browser.links.find_by_href('/plinth/apps/kiwix/content/add/').first.click()
    browser.attach_file('kiwix-file', file_name)
    functional.submit(browser, form_class='form-kiwix')


def _is_content_package_available(browser, title) -> bool:
    browser.visit(f'{_default_url}/kiwix')
    sleep(1)  # Allow time for the books to appear
    titles = browser.find_by_id('book__title')
    print(len(titles))
    print([title.value for title in titles])
    return any(map(lambda e: e.value == title, titles))


def _is_content_package_listed(browser, name) -> bool:
    functional.nav_to_module(browser, 'kiwix')
    links_found = browser.links.find_by_partial_href(f'/kiwix/viewer#{name}')
    return len(links_found) == 1


def _delete_content_package(browser, zim_id):
    functional.nav_to_module(browser, 'kiwix')
    link = browser.links.find_by_href(
        f'/plinth/apps/kiwix/content/{zim_id}/delete/')
    if not link:
        raise ValueError('ZIM file missing!')
    link.first.click()
    functional.submit(browser, form_class='form-delete')


# TODO Add test to check that Kiwix can be viewed without logging in.
