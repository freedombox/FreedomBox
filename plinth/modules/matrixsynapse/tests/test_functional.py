# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for matrixsynapse app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.matrixsynapse]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.set_domain_name(session_browser, 'mydomain.example')
    functional.install(session_browser, 'matrixsynapse')
    functional.app_select_domain_name(session_browser, 'matrixsynapse',
                                      'mydomain.example')
    yield
    functional.app_disable(session_browser, 'matrixsynapse')


def test_enable_disable(session_browser):
    """Test enabling the app."""
    functional.app_disable(session_browser, 'matrixsynapse')

    functional.app_enable(session_browser, 'matrixsynapse')
    assert functional.service_is_running(session_browser, 'matrixsynapse')

    functional.app_disable(session_browser, 'matrixsynapse')
    assert functional.service_is_not_running(session_browser, 'matrixsynapse')
