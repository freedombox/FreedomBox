# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mldonkey app.
"""

import pytest
from plinth.tests import functional

pytestmark = [
    pytest.mark.apps, pytest.mark.mldonkey, pytest.mark.sso, pytest.mark.skip
]


class TestMldonkeyApp(functional.BaseAppTests):
    app_name = 'mldonkey'
    has_service = True
    has_web = True

    def test_upload(self, session_browser):
        """Test uploading an ed2k file to mldonkey."""
        functional.app_enable(session_browser, 'mldonkey')
        _remove_all_ed2k_files(session_browser)
        _upload_sample_ed2k_file(session_browser)
        assert _get_number_of_ed2k_files(session_browser) == 1

    def test_backup_restore(self, session_browser):
        """Test backup and restore of ed2k files."""
        functional.app_enable(session_browser, 'mldonkey')
        _remove_all_ed2k_files(session_browser)
        _upload_sample_ed2k_file(session_browser)
        functional.backup_create(session_browser, 'mldonkey', 'test_mldonkey')

        _remove_all_ed2k_files(session_browser)
        functional.backup_restore(session_browser, 'mldonkey', 'test_mldonkey')

        assert functional.service_is_running(session_browser, 'mldonkey')
        assert _get_number_of_ed2k_files(session_browser) == 1


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
        functional.eventually(output_frame.find_by_css, ['.downloaded'])
        return len(output_frame.find_by_css('.dl-1')) + len(
            output_frame.find_by_css('.dl-2'))
