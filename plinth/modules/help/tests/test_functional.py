# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for help app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.help]

# TODO Scenario: Visit the wiki
# TODO Scenario: Visit the mailing list
# TODO Scenario: Visit the IRC channel
# TODO Scenario: View the manual
# TODO Scenario: View the about page


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_view_status_logs(session_browser):
    """Test viewing the status logs."""
    _go_to_status_logs(session_browser)
    assert _are_status_logs_shown(session_browser)


def _go_to_status_logs(browser):
    functional.visit(browser, '/plinth/help/status-log/')


def _are_status_logs_shown(browser):
    status_log = browser.find_by_css('.status-log').first.text
    return ('-- No entries --' in status_log
            or status_log.strip().splitlines())
