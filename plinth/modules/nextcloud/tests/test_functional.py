# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for Nextcloud app."""

import time
import urllib

import pytest
from selenium.webdriver.common.keys import Keys

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.nextcloud]

PASSWORD = 'kai8wahTei'


class TestNextcloudApp(functional.BaseAppTests):
    app_name = 'nextcloud'
    has_service = True

    def install_and_setup(self, session_browser):
        """Install app and set the domain."""
        super().install_and_setup(session_browser)
        functional.app_enable(session_browser, self.app_name)
        default_url = functional.config['DEFAULT']['url']
        parse_result = urllib.parse.urlparse(default_url)
        override_domain = parse_result.hostname
        override_domain += f':{parse_result.port}' if parse_result.port else ''
        session_browser.find_by_id('id_override_domain').fill(override_domain)
        session_browser.find_by_id('id_admin_password').fill(PASSWORD)
        functional.submit(session_browser, form_class='form-configuration')

    def test_create_folder(self, session_browser, background):
        """Test that creating a folder works."""
        folder_name = 'TestFolder'
        _visit_files_app(session_browser)

        _remove_folder(session_browser, folder_name)
        assert not _is_folder_present(session_browser, folder_name)

        _create_folder(session_browser, folder_name)
        assert _is_folder_present(session_browser, folder_name)

    def test_backup_restore(self, session_browser):
        """Test that backup and restore operations work on the app."""
        folder_name = 'TestBackupFolder'
        _visit_files_app(session_browser)
        if not _is_folder_present(session_browser, folder_name):
            _create_folder(session_browser, folder_name)

        super().test_backup_restore(session_browser)

        _visit_files_app(session_browser)
        assert _is_folder_present(session_browser, folder_name)


def _login(browser):
    """Login to Nextcloud interface."""
    functional.visit(browser, '/nextcloud/')
    if not browser.find_by_css('.login-form'):
        return

    browser.find_by_id('user').fill('nextcloud-admin')
    browser.find_by_id('password').fill(PASSWORD)
    functional.submit(browser, form_class='login-form')


def _visit_files_app(browser):
    """Login to Nextcloud and visit the files app."""
    _login(browser)
    functional.visit(browser, '/nextcloud/apps/files/files')
    # Close the welcome model dialog if it is present
    browser.find_by_tag('html').first.type(Keys.ESCAPE)
    time.sleep(1)  # Allow the model dialog to close.


def _remove_folder(browser, folder_name):
    """Remove a folder from Nextcloud files app."""
    # Select the folder
    xpath = f'//tr[{_class("files-list__row")} and ' \
        f'.//*[{_class("files-list__row-name-")} and ' \
        f'contains(text(),"{folder_name}")]]' \
        f'//span[{_class("checkbox-content-checkbox")}]'
    matches = browser.find_by_xpath(xpath)
    if not matches:
        return

    matches.first.check()

    # Click on '...' more actions button
    xpath = '//button[@aria-label="Actions"]'
    browser.find_by_xpath(xpath).first.click()

    # Click on 'Delete folder' pop down menu item
    xpath = '//button[.//span[contains(text(),"Delete folder")]]'
    browser.find_by_xpath(xpath).first.click()


def _is_folder_present(browser, folder_name):
    """Return whether a folder with given name exists."""
    xpath = f'//tr[{_class("files-list__row")}]' \
        f'//*[{_class("files-list__row-name-")} and ' \
        f'contains(text(),"{folder_name}")]'
    return bool(browser.find_by_xpath(xpath))


def _class(klass):
    """Return xpath snippet for matching class."""
    return f'contains(concat(" ",@class," "), " {klass} ")'


def _create_folder(browser, folder_name):
    """Create a folder in the Nextcloud files app."""
    # Click on the '+ New' button in the header
    xpath = f'//div[{_class("action-item")} and @menu-title="New"]//button'
    browser.find_by_xpath(xpath).first.click()

    # Click on the 'New folder' pop down menu item
    xpath = f'//button[{_class("action-button")} and ' \
        './span[text()="New folder"]]'
    browser.find_by_xpath(xpath).first.click()

    # Get the 'Create new folder' dialog box
    xpath = f'//div[{_class("dialog__modal")} and ' \
        './/h2[text()="Create new folder"]]'
    dialog = browser.find_by_xpath(xpath).first

    # Enter the folder name into text box 'Folder name'
    xpath = f'.//input[{_class("input-field__input")}]'
    dialog.find_by_xpath(xpath).first.fill(folder_name)

    # Press the 'Create' button
    xpath = './/button[.//*[contains(text(),"Create")]]'
    dialog.find_by_xpath(xpath).first.click()
