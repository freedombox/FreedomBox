# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for syncthing app.
"""

import time

import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.syncthing, pytest.mark.sso]


class TestSyncthingApp(functional.BaseAppTests):
    app_name = 'syncthing'
    has_service = True
    has_web = True

    def test_notifications(self, session_browser):
        """Test that authentication and usage reporting notifications are not
        shown."""
        functional.app_enable(session_browser, self.app_name)
        functional.access_url(session_browser, self.app_name)
        _assert_usage_report_notification_not_shown(session_browser)
        _assert_authentication_notification_not_shown(session_browser)

    def test_add_remove_folder(self, session_browser):
        """Test adding and removing a folder."""
        functional.app_enable(session_browser, self.app_name)
        if _folder_is_present(session_browser, 'Test'):
            _remove_folder(session_browser, 'Test')

        _add_folder(session_browser, 'Test', '/tmp')
        assert _folder_is_present(session_browser, 'Test')

        _remove_folder(session_browser, 'Test')
        assert not _folder_is_present(session_browser, 'Test')

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backup and restore of app data."""
        functional.app_enable(session_browser, self.app_name)
        if _folder_is_present(session_browser, 'Test'):
            _remove_folder(session_browser, 'Test')

        _add_folder(session_browser, 'Test', '/tmp')
        functional.backup_create(session_browser, self.app_name,
                                 'test_syncthing')

        _remove_folder(session_browser, 'Test')
        time.sleep(1)  # Helps with browsing away in next step
        functional.backup_restore(session_browser, self.app_name,
                                  'test_syncthing')

        assert _folder_is_present(session_browser, 'Test')

    def test_user_group_access(self, session_browser):
        """Test that only users in syncthing-access group can access syncthing
        site."""
        functional.app_enable(session_browser, self.app_name)
        if not functional.user_exists(session_browser, 'syncthinguser'):
            functional.create_user(session_browser, 'syncthinguser',
                                   groups=['syncthing-access'])
        if not functional.user_exists(session_browser, 'nogroupuser'):
            functional.create_user(session_browser, 'nogroupuser')

        functional.login_with_account(session_browser, functional.base_url,
                                      'syncthinguser')
        assert functional.is_available(session_browser, self.app_name)

        functional.login_with_account(session_browser, functional.base_url,
                                      'nogroupuser')
        assert not functional.is_available(session_browser, self.app_name)

        functional.login(session_browser)


def _assert_usage_report_notification_not_shown(session_browser):
    _load_main_interface(session_browser)
    assert session_browser.find_by_id('ur').visible is False


def _assert_authentication_notification_not_shown(session_browser):
    _load_main_interface(session_browser)
    assert bool(session_browser.find_by_css(
        '#authenticationUserAndPassword *')) is False


def _load_main_interface(browser):
    """Close the dialog boxes that many popup after visiting the URL."""
    functional.access_url(browser, 'syncthing')

    def service_is_available():
        if browser.is_element_present_by_xpath(
                '//h1[text()="Service Unavailable"]'):
            functional.access_url(browser, 'syncthing')
            return False

        return True

    # After a backup restore, service may not be available immediately
    functional.eventually(service_is_available)

    # Wait for javascript loading process to complete
    functional.eventually(lambda: browser.evaluate_script(
        'angular.element("[ng-controller=SyncthingController]").scope()'
        '.thisDevice().name'))

    # Give browser additional time to setup site
    time.sleep(1)


def _folder_is_present(browser, folder_name):
    """Return whether a folder is present in Syncthing."""
    _load_main_interface(browser)
    folder_names = browser.find_by_css('#folders .panel-title-text span')
    folder_names = [folder_name.text for folder_name in folder_names]
    return folder_name in folder_names


def _add_folder(browser, folder_name, folder_path):
    """Add a new folder to Synthing."""
    _load_main_interface(browser)
    add_folder_xpath = '//button[contains(@ng-click, "addFolder")]'
    browser.find_by_xpath(add_folder_xpath).click()

    folder_dialog = browser.find_by_id('editFolder').first
    functional.eventually(lambda: folder_dialog.visible)
    browser.find_by_id('folderLabel').fill(folder_name)
    browser.find_by_id('folderPath').fill(folder_path)
    save_folder_xpath = './/button[contains(@ng-click, "saveFolder")]'
    folder_dialog.find_by_xpath(save_folder_xpath).first.click()
    functional.eventually(lambda: not folder_dialog.visible)


def _remove_folder(browser, folder_name):
    """Remove a folder from Synthing."""
    _load_main_interface(browser)

    # Find folder
    folder = None
    for current_folder in browser.find_by_css('#folders > .panel'):
        name = current_folder.find_by_css('.panel-title-text span').first.text
        if name == folder_name:
            folder = current_folder
            break

    # Edit folder button
    folder.find_by_css('button.panel-heading').first.click()
    functional.eventually(lambda: folder.find_by_css('div.collapse.in'))
    edit_folder_xpath = './/button[contains(@ng-click, "editFolder")]'
    edit_folder_button = folder.find_by_xpath(edit_folder_xpath).first
    edit_folder_button.scroll_to()
    edit_folder_button.click()

    # Edit folder dialog
    folder_dialog = browser.find_by_id('editFolder').first
    functional.eventually(lambda: folder_dialog.visible)
    remove_button_xpath = './/button[contains(@data-target, "remove-folder")]'
    folder_dialog.find_by_xpath(remove_button_xpath).first.click()

    # Remove confirmation dialog
    remove_folder_dialog = browser.find_by_id('remove-folder-confirmation')
    functional.eventually(lambda: remove_folder_dialog.visible)
    remove_button_xpath = './/button[contains(@ng-click, "deleteFolder")]'
    remove_folder_dialog.find_by_xpath(remove_button_xpath).first.click()

    functional.eventually(lambda: not folder_dialog.visible)
