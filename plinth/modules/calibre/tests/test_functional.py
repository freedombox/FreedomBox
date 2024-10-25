# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for calibre app.
"""

import pathlib
import time

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.sso, pytest.mark.calibre]


class TestCalibreApp(functional.BaseAppTests):
    app_name = 'calibre'
    has_service = True
    has_web = True

    def test_add_delete_library(self, session_browser):
        """Test adding/deleting a new library."""
        functional.app_enable(session_browser, 'calibre')
        _delete_library(session_browser, 'FunctionalTest', True)

        _add_library(session_browser, 'FunctionalTest')
        assert _is_library_available(session_browser, 'FunctionalTest')

        _delete_library(session_browser, 'FunctionalTest')
        assert not _is_library_available(session_browser, 'FunctionalTest')

    def test_add_delete_book(self, session_browser):
        """Test adding/delete book in the library."""
        functional.app_enable(session_browser, 'calibre')
        _add_library(session_browser, 'FunctionalTest')
        _delete_book(session_browser, 'FunctionalTest', 'sample.txt', True)

        _add_book(session_browser, 'FunctionalTest', 'sample.txt')
        assert _is_book_available(session_browser, 'FunctionalTest',
                                  'sample.txt')

        _delete_book(session_browser, 'FunctionalTest', 'sample.txt')
        assert not _is_book_available(session_browser, 'FunctionalTest',
                                      'sample.txt')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backing up and restoring."""
        functional.app_enable(session_browser, 'calibre')
        _add_library(session_browser, 'FunctionalTest')
        functional.backup_create(session_browser, 'calibre', 'test_calibre')
        _delete_library(session_browser, 'FunctionalTest')
        functional.backup_restore(session_browser, 'calibre', 'test_calibre')
        assert _is_library_available(session_browser, 'FunctionalTest')


def _add_library(browser, name):
    """Add a new library."""
    if _is_library_available(browser, name):
        return

    browser.links.find_by_href(
        '/plinth/apps/calibre/library/create/').first.click()
    browser.find_by_id('id_calibre-name').fill(name)
    functional.submit(browser, form_class='form-calibre')


def _delete_library(browser, name, ignore_missing=False):
    """Delete a library."""
    functional.nav_to_module(browser, 'calibre')
    link = browser.links.find_by_href(
        f'/plinth/apps/calibre/library/{name}/delete/')
    if not link:
        if ignore_missing:
            return

        raise ValueError('Library not found')

    link.first.click()
    functional.submit(browser, form_class='form-delete')


def _is_library_available(browser, name):
    """Return whether a library is present in the list of libraries."""
    functional.nav_to_module(browser, 'calibre')
    link = browser.links.find_by_href(
        f'/plinth/apps/calibre/library/{name}/delete/')
    return bool(link)


def _visit_library(browser, name):
    """Open the page for the library."""
    functional.visit(browser, '/calibre/')

    # Calibre interface will be available a short time after restarting the
    # service.
    def _service_available():
        unavailable_xpath = '//h1[contains(text(), "Service Unavailable")]'
        available = not browser.find_by_xpath(unavailable_xpath)
        if not available:
            time.sleep(0.5)
            functional.visit(browser, '/calibre/')

        return available

    functional.eventually(_service_available)

    def _library_available():
        """Refresh until the expected library is available."""
        available = browser.find_by_css(
            f'.calibre-push-button[data-lid="{name}"]')
        if not available:
            time.sleep(0.5)
            functional.visit(browser, '/calibre')

        return available

    functional.eventually(_library_available)
    link = browser.find_by_css(f'.calibre-push-button[data-lid="{name}"]')
    if not link:
        raise ValueError('Library not found')

    link.first.click()
    functional.eventually(browser.find_by_css, ['.book-list-cover-grid'])


def _add_book(browser, library_name, book_name):
    """Add a book to the library through Calibre interface."""
    _visit_library(browser, library_name)
    add_button = browser.find_by_css('a[data-button-icon="plus"]')
    add_button.first.click()

    functional.eventually(browser.find_by_xpath,
                          ['//span[contains(text(), "Add books")]'])
    browser.execute_script(
        '''document.querySelector('input[type="file"]').setAttribute(
        'name', 'test-book-upload');''')

    file_path = pathlib.Path(__file__).parent / f'data/{book_name}'
    browser.attach_file('test-book-upload', [str(file_path)])
    functional.eventually(browser.find_by_xpath,
                          ['//span[contains(text(), "Added successfully")]'])


def _delete_book(browser, library_name, book_name, ignore_missing=False):
    """Delete a book from the library through Calibre interface."""
    _visit_library(browser, library_name)
    book_name = book_name.partition('.')[0]
    book = browser.find_by_xpath(f'//a[contains(@title, "{book_name}")]')
    if not book:
        if ignore_missing:
            return

        raise Exception('Book not found')

    book.first.click()
    delete_button = browser.find_by_css('a[data-button-icon="trash"]')
    delete_button.first.click()

    dialog = browser.find_by_id('modal-container').first
    functional.eventually(lambda: dialog.visible)
    ok_button = browser.find_by_xpath('//span[contains(text(), "OK")]')
    ok_button.first.click()


def _is_book_available(browser, library_name, book_name):
    """Return whether a book is present in Calibre interface."""
    _visit_library(browser, library_name)
    book_name = book_name.partition('.')[0]
    book = browser.find_by_xpath(f'//a[contains(@title, "{book_name}")]')
    return bool(book)
