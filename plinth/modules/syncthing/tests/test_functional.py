# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for syncthing app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('syncthing.feature')


@given(parsers.parse('syncthing folder {folder_name:w} is not present'))
def syncthing_folder_not_present(session_browser, folder_name):
    if _folder_is_present(session_browser, folder_name):
        _remove_folder(session_browser, folder_name)


@given(
    parsers.parse(
        'folder {folder_path:S} is present as syncthing folder {folder_name:w}'
    ))
def syncthing_folder_present(session_browser, folder_name, folder_path):
    if not _folder_is_present(session_browser, folder_name):
        _add_folder(session_browser, folder_name, folder_path)


@when(
    parsers.parse(
        'I add a folder {folder_path:S} as syncthing folder {folder_name:w}'))
def syncthing_add_folder(session_browser, folder_name, folder_path):
    _add_folder(session_browser, folder_name, folder_path)


@when(parsers.parse('I remove syncthing folder {folder_name:w}'))
def syncthing_remove_folder(session_browser, folder_name):
    _remove_folder(session_browser, folder_name)


@then(parsers.parse('syncthing folder {folder_name:w} should be present'))
def syncthing_assert_folder_present(session_browser, folder_name):
    assert _folder_is_present(session_browser, folder_name)


@then(parsers.parse('syncthing folder {folder_name:w} should not be present'))
def syncthing_assert_folder_not_present(session_browser, folder_name):
    assert not _folder_is_present(session_browser, folder_name)


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
    browser.execute_script('''
        document.is_ui_online = false;
        var old_console_log = console.log;
        console.log = function(message) {
            old_console_log.apply(null, arguments);
            if (message == 'UIOnline') {
                document.is_ui_online = true;
                console.log = old_console_log;
            }
        };
    ''')
    functional.eventually(
        lambda: browser.evaluate_script('document.is_ui_online'), timeout=5)

    # Dismiss the Usage Reporting consent dialog
    functional.eventually(browser.find_by_id, ['ur'])
    usage_reporting = browser.find_by_id('ur').first
    functional.eventually(lambda: usage_reporting.visible, timeout=2)
    if usage_reporting.visible:
        yes_xpath = './/button[contains(@ng-click, "declineUR")]'
        usage_reporting.find_by_xpath(yes_xpath).first.click()
        functional.eventually(lambda: not usage_reporting.visible)


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
