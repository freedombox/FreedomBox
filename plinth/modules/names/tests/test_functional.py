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


def test_change_domain_name(session_browser):
    """Test changing the domain name."""
    functional.domain_remove(session_browser, 'mydomain.example')
    functional.domain_add(session_browser, 'mydomain.example')
    assert 'mydomain.example' in functional.domain_list(session_browser)

    # Capitalization is ignored.
    functional.domain_remove(session_browser, 'mydomain2.example')
    functional.domain_add(session_browser, 'Mydomain2.example')
    assert 'mydomain2.example' in functional.domain_list(session_browser)
