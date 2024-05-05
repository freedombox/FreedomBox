# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for TiddlyWiki app."""

import pathlib

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.tiddlywiki]

wiki_name = 'Engineering Daybook'
file_name = 'Engineering_Daybook.html'


class TestTiddlyWikiApp(functional.BaseAppTests):
    app_name = 'tiddlywiki'
    has_service = False
    has_web = True

    def _create_wiki_file(self, session_browser):
        """Add a wiki to using the 'Create' functionality."""
        functional.nav_to_module(session_browser, 'tiddlywiki')

        wiki_link = f'/tiddlywiki/{file_name}'
        if self._get_links_in_app_page(session_browser, wiki_link):
            return

        session_browser.links.find_by_href(
            '/plinth/apps/tiddlywiki/create/').first.click()
        session_browser.find_by_id('id_tiddlywiki-name').fill(wiki_name)
        functional.submit(session_browser, form_class='form-tiddlywiki')

    def _get_links_in_app_page(self, session_browser, link):
        """Return the links matching a href in the app page."""
        functional.nav_to_module(session_browser, 'tiddlywiki')
        return session_browser.links.find_by_href(link)

    def _get_links_in_apache_listing(self, session_browser, link):
        """Return the links matching a href in the index page."""
        default_url = functional.config['DEFAULT']['url']
        session_browser.visit(f'{default_url}/tiddlywiki')
        return session_browser.links.find_by_href(link)

    def _assert_wiki_present(self, session_browser, file_name, present=True):
        """Assert that a wiki is present."""
        wiki_link = f'/tiddlywiki/{file_name}'
        assert bool(self._get_links_in_app_page(session_browser,
                                                wiki_link)) == present
        assert bool(
            self._get_links_in_apache_listing(session_browser,
                                              file_name)) == present

    def _assert_wiki_works(self, session_browser, file_name):
        """Assert that wiki loads and run as expected."""
        wiki_link = f'/tiddlywiki/{file_name}'
        default_url = functional.config['DEFAULT']['url']
        session_browser.visit(f'{default_url}{wiki_link}')
        links = session_browser.links.find_by_href(
            'https://tiddlywiki.com/#GettingStarted')
        assert len(links) == 1

    def test_wiki_file_access(self, session_browser):
        """Test creating a new wiki file."""
        self._create_wiki_file(session_browser)

        self._assert_wiki_present(session_browser, file_name)
        self._assert_wiki_works(session_browser, file_name)

    def test_rename_wiki_file(self, session_browser):
        """Test changing the name of a wiki file."""
        self._create_wiki_file(session_browser)

        new_wiki_name = 'A Midsummer Night\'s Dream'
        new_file_name = 'A_Midsummer_Nights_Dream.html'
        self._get_links_in_app_page(
            session_browser,
            '/plinth/apps/tiddlywiki/' + file_name + '/rename/').first.click()
        session_browser.find_by_id('id_tiddlywiki-new_name').fill(
            new_wiki_name)
        functional.submit(session_browser, form_class='form-tiddlywiki')

        self._assert_wiki_present(session_browser, new_file_name)
        self._assert_wiki_works(session_browser, new_file_name)

    def test_upload_wiki_file(self, session_browser):
        """Test uploading an existing wiki file."""
        _test_data_dir = pathlib.Path(__file__).parent / 'data'
        test_wiki_file = str(_test_data_dir / 'dummy_wiki.html')

        session_browser.links.find_by_href(
            '/plinth/apps/tiddlywiki/upload/').first.click()
        session_browser.attach_file('tiddlywiki-file', test_wiki_file)
        functional.submit(session_browser, form_class='form-tiddlywiki')

        self._assert_wiki_present(session_browser, 'dummy_wiki.html')

    def test_delete_wiki_file(self, session_browser):
        """Test deleting an existing wiki file"""
        self._create_wiki_file(session_browser)

        self._get_links_in_app_page(
            session_browser,
            '/plinth/apps/tiddlywiki/' + file_name + '/delete/').first.click()
        functional.submit(session_browser, form_class='form-delete')

        self._assert_wiki_present(session_browser, file_name, present=False)
