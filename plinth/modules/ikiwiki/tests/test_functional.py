# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ikiwiki app.
"""

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.ikiwiki]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'ikiwiki')
    yield
    functional.app_disable(session_browser, 'ikiwiki')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'ikiwiki')

    functional.app_enable(session_browser, 'ikiwiki')
    assert functional.is_available(session_browser, 'ikiwiki')

    functional.app_disable(session_browser, 'ikiwiki')
    assert not functional.is_available(session_browser, 'ikiwiki')


@pytest.mark.backups
def test_backup_and_restore(session_browser):
    functional.app_enable(session_browser, 'ikiwiki')
    _create_wiki_if_needed(session_browser)
    functional.backup_create(session_browser, 'ikiwiki', 'test_ikiwiki')

    _delete_wiki(session_browser)
    functional.backup_restore(session_browser, 'ikiwiki', 'test_ikiwiki')

    assert _wiki_exists(session_browser)


def _create_wiki_if_needed(browser):
    """Create wiki if it does not exist."""
    functional.nav_to_module(browser, 'ikiwiki')
    wiki = browser.links.find_by_href('/ikiwiki/wiki')
    if not wiki:
        browser.links.find_by_href(
            '/plinth/apps/ikiwiki/create/').first.click()
        browser.find_by_id('id_ikiwiki-name').fill('wiki')
        browser.find_by_id('id_ikiwiki-admin_name').fill(
            functional.config['DEFAULT']['username'])
        browser.find_by_id('id_ikiwiki-admin_password').fill(
            functional.config['DEFAULT']['password'])
        functional.submit(browser)


def _delete_wiki(browser):
    """Delete wiki."""
    functional.nav_to_module(browser, 'ikiwiki')
    browser.links.find_by_href(
        '/plinth/apps/ikiwiki/wiki/delete/').first.click()
    functional.submit(browser)


def _wiki_exists(browser):
    """Check whether the wiki exists."""
    functional.nav_to_module(browser, 'ikiwiki')
    wiki = browser.links.find_by_href('/ikiwiki/wiki')
    return bool(wiki)
