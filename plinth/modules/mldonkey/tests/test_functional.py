# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mldonkey app.
"""

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('mldonkey.feature')


@when('all ed2k files are removed from mldonkey')
def mldonkey_remove_all_ed2k_files(session_browser):
    _remove_all_ed2k_files(session_browser)


@when('I upload a sample ed2k file to mldonkey')
def mldonkey_upload_sample_ed2k_file(session_browser):
    _upload_sample_ed2k_file(session_browser)


@then(
    parsers.parse(
        'there should be {ed2k_files_number:d} ed2k files listed in mldonkey'))
def mldonkey_assert_number_of_ed2k_files(session_browser, ed2k_files_number):
    assert ed2k_files_number == _get_number_of_ed2k_files(session_browser)


def _submit_command(browser, command):
    """Submit a command to mldonkey."""
    with browser.get_iframe('commands') as commands_frame:
        commands_frame.find_by_css('.txt2').fill(command)
        commands_frame.find_by_css('.but2').click()


def _remove_all_ed2k_files(browser):
    """Remove all ed2k files from mldonkey."""
    functional.visit(browser, '/mldonkey/')
    _submit_command(browser, 'cancel all')
    _submit_command(browser, 'confirm yes')


def _upload_sample_ed2k_file(browser):
    """Upload a sample ed2k file into mldonkey."""
    functional.visit(browser, '/mldonkey/')
    dllink_command = 'dllink ed2k://|file|foo.bar|123|' \
        '0123456789ABCDEF0123456789ABCDEF|/'
    _submit_command(browser, dllink_command)


def _get_number_of_ed2k_files(browser):
    """Return the number of ed2k files currently in mldonkey."""
    functional.visit(browser, '/mldonkey/')

    with browser.get_iframe('commands') as commands_frame:
        commands_frame.find_by_xpath(
            '//tr//td[contains(text(), "Transfers")]').click()

    with browser.get_iframe('output') as output_frame:
        return len(output_frame.find_by_css('.dl-1')) + len(
            output_frame.find_by_css('.dl-2'))
