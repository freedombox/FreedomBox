# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ikiwiki app.
"""

from pytest_bdd import scenarios, then, when

from plinth.tests import functional

scenarios('ikiwiki.feature')


@when('there is an ikiwiki wiki')
def ikiwiki_create_wiki_if_needed(session_browser):
    _create_wiki_if_needed(session_browser)


@when('I delete the ikiwiki wiki')
def ikiwiki_delete_wiki(session_browser):
    _delete_wiki(session_browser)


@then('the ikiwiki wiki should be restored')
def ikiwiki_should_exist(session_browser):
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
