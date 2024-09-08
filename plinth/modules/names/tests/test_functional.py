# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for names app."""

import pytest

from plinth.tests import functional

pytestmark = [
    pytest.mark.system, pytest.mark.essential, pytest.mark.domain,
    pytest.mark.names
]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_change_hostname(session_browser):
    """Test changing the hostname."""
    functional.set_hostname(session_browser, 'mybox')
    assert _get_hostname(session_browser) == 'mybox'


def _get_hostname(browser):
    functional.visit(browser, '/plinth/sys/names/hostname/')
    return browser.find_by_id('id_hostname-hostname').value
