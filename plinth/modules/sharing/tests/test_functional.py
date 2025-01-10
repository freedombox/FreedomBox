# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for sharing app.
"""

import pytest
import splinter

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.sharing]


class TestSharingApp(functional.BaseAppTests):
    app_name = 'sharing'
    has_service = False
    has_web = False
    check_diagnostics = False

    def test_add_remove_share(self, session_browser):
        """Test adding and removing a share."""
        _remove_share(session_browser, 'tmp')
        _add_share(session_browser, 'tmp', '/tmp', 'admin')
        _verify_share(session_browser, 'tmp', '/tmp', 'admin')
        _access_share(session_browser, 'tmp')

        _remove_share(session_browser, 'tmp')
        _verify_invalid_share(session_browser, 'tmp')
        _verify_nonexistant_share(session_browser, 'tmp')

    def test_edit_share(self, session_browser):
        """Test editing a share."""
        _remove_share(session_browser, 'tmp')
        _remove_share(session_browser, 'boot')

        _add_share(session_browser, 'tmp', '/tmp', 'admin')
        _edit_share(session_browser, 'tmp', 'boot', '/boot', 'admin')

        _verify_invalid_share(session_browser, 'tmp')
        _verify_nonexistant_share(session_browser, 'tmp')

        _verify_share(session_browser, 'boot', '/boot', 'admin')
        _access_share(session_browser, 'boot')

    def test_share_permissions(self, session_browser):
        """Test share permissions."""
        _remove_share(session_browser, 'tmp')
        _add_share(session_browser, 'tmp', '/tmp', 'syncthing-access')
        _verify_share(session_browser, 'tmp', '/tmp', 'syncthing-access')
        _verify_inaccessible_share(session_browser, 'tmp')

        _make_share_public(session_browser, 'tmp')
        functional.logout(session_browser)
        assert functional.is_available(session_browser, 'share_tmp')
        functional.login(session_browser)

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore."""
        _remove_share(session_browser, 'tmp')
        _add_share(session_browser, 'tmp', '/tmp', 'admin')
        functional.backup_create(session_browser, 'sharing', 'test_sharing')

        _remove_share(session_browser, 'tmp')
        functional.backup_restore(session_browser, 'sharing', 'test_sharing')

        _verify_share(session_browser, 'tmp', '/tmp', 'admin')
        _access_share(session_browser, 'tmp')


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
    functional.submit(browser, form_class='form-add-edit')


def _edit_share(browser, old_name, new_name, path, group):
    """Edit a share in sharing app."""
    row = _get_share(browser, old_name)
    functional.click_and_wait(browser, row.find_by_css('.share-edit').first)
    browser.fill('sharing-name', new_name)
    browser.fill('sharing-path', path)
    browser.find_by_css('#id_sharing-groups input').uncheck()
    browser.find_by_css(
        '#id_sharing-groups input[value="{}"]'.format(group)).check()
    functional.submit(browser, form_class='form-add-edit')


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
    functional.click_and_wait(browser, row.find_by_css('.share-edit').first)
    browser.find_by_id('id_sharing-is_public').check()
    functional.submit(browser, form_class='form-add-edit')


def _verify_invalid_share(browser, name):
    with pytest.raises(splinter.exceptions.ElementDoesNotExist):
        _get_share(browser, name)


def _verify_nonexistant_share(browser, name):
    """Verify that given URL for a given share name is a 404."""
    functional.visit(browser, f'/share/{name}')
    functional.eventually(lambda: '404' in browser.title)


def _verify_inaccessible_share(browser, name):
    """Verify that given URL for a given share name denies permission."""
    functional.visit(browser, f'/share/{name}')
    functional.eventually(lambda: '/plinth' in browser.url, args=[])
