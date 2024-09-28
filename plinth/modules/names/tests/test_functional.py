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
    functional.set_domain_name(session_browser, 'mydomain.example')
    assert _get_domain_name(session_browser) == 'mydomain.example'

    # Capitalization is ignored.
    functional.set_domain_name(session_browser, 'Mydomain.example')
    assert _get_domain_name(session_browser) == 'mydomain.example'


def _get_domain_name(browser):
    functional.visit(browser, '/plinth/sys/names/domains/')
    return browser.find_by_id('id_domain-name-domain_name').value
