# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for sharing app.
"""

import pytest
import splinter
from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('sharing.feature')


@given(parsers.parse('share {name:w} is not available'))
def remove_share(session_browser, name):
    _remove_share(session_browser, name)


@when(parsers.parse('I add a share {name:w} from path {path} for {group:S}'))
def add_share(session_browser, name, path, group):
    _add_share(session_browser, name, path, group)


@when(
    parsers.parse('I edit share {old_name:w} to {new_name:w} from path {path} '
                  'for {group:w}'))
def edit_share(session_browser, old_name, new_name, path, group):
    _edit_share(session_browser, old_name, new_name, path, group)


@when(parsers.parse('I remove share {name:w}'))
def remove_share2(session_browser, name):
    _remove_share(session_browser, name)


@when(parsers.parse('I edit share {name:w} to be public'))
def edit_share_public_access(session_browser, name):
    _make_share_public(session_browser, name)


@then(
    parsers.parse(
        'the share {name:w} should be listed from path {path} for {group:S}'))
def verify_share(session_browser, name, path, group):
    _verify_share(session_browser, name, path, group)


@then(parsers.parse('the share {name:w} should not be listed'))
def verify_invalid_share(session_browser, name):
    with pytest.raises(splinter.exceptions.ElementDoesNotExist):
        _get_share(session_browser, name)


@then(parsers.parse('the share {name:w} should be accessible'))
def access_share(session_browser, name):
    _access_share(session_browser, name)


@then(parsers.parse('the share {name:w} should not exist'))
def verify_nonexistant_share(session_browser, name):
    _verify_nonexistant_share(session_browser, name)


@then(parsers.parse('the share {name:w} should not be accessible'))
def verify_inaccessible_share(session_browser, name):
    _verify_inaccessible_share(session_browser, name)


def _remove_share(browser, name):
    """Remove a share in sharing app."""
    try:
        share_row = _get_share(browser, name)
    except splinter.exceptions.ElementDoesNotExist:
        pass
    else:
        share_row.find_by_css('.share-remove')[0].click()


def _add_share(browser, name, path, group):
    """Add a share in sharing app."""
    functional.visit(browser, '/plinth/apps/sharing/add/')
    browser.fill('sharing-name', name)
    browser.fill('sharing-path', path)
    browser.find_by_css(
        '#id_sharing-groups input[value="{}"]'.format(group)).check()
    functional.submit(browser)


def _edit_share(browser, old_name, new_name, path, group):
    """Edit a share in sharing app."""
    row = _get_share(browser, old_name)
    with functional.wait_for_page_update(browser):
        row.find_by_css('.share-edit')[0].click()
    browser.fill('sharing-name', new_name)
    browser.fill('sharing-path', path)
    browser.find_by_css('#id_sharing-groups input').uncheck()
    browser.find_by_css(
        '#id_sharing-groups input[value="{}"]'.format(group)).check()
    functional.submit(browser)


def _get_share(browser, name):
    """Return the row for a given share."""
    functional.visit(browser, '/plinth/apps/sharing/')
    return browser.find_by_id('share-{}'.format(name))[0]


def _verify_share(browser, name, path, group):
    """Verfiy that a share exists in list of shares."""
    href = f'{functional.base_url}/share/{name}'
    url = f'/share/{name}'
    row = _get_share(browser, name)
    assert row.find_by_css('.share-name')[0].text == name
    assert row.find_by_css('.share-path')[0].text == path
    assert row.find_by_css('.share-url a')[0]['href'] == href
    assert row.find_by_css('.share-url a')[0].text == url
    assert row.find_by_css('.share-groups')[0].text == group


def _access_share(browser, name):
    """Visit a share and see if it is accessible."""
    row = _get_share(browser, name)
    url = row.find_by_css('.share-url a')[0]['href']
    browser.visit(url)
    assert '/share/{}'.format(name) in browser.title


def _make_share_public(browser, name):
    """Make share publicly accessible."""
    row = _get_share(browser, name)
    with functional.wait_for_page_update(browser):
        row.find_by_css('.share-edit')[0].click()
    browser.find_by_id('id_sharing-is_public').check()
    functional.submit(browser)


def _verify_nonexistant_share(browser, name):
    """Verify that given URL for a given share name is a 404."""
    functional.visit(browser, f'/share/{name}')
    assert '404' in browser.title


def _verify_inaccessible_share(browser, name):
    """Verify that given URL for a given share name denies permission."""
    functional.visit(browser, f'/share/{name}')
    functional.eventually(lambda: '/plinth' in browser.url, args=[])
