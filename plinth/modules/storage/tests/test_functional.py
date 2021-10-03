# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for storage app.
"""
import pytest
from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.storage]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login."""
    functional.login(session_browser)


def test_list_disks(session_browser):
    """Test that root disk is shown on storage page."""
    if functional.running_inside_container:
        pytest.skip('Storage doesn\'t work inside a container')
    else:
        functional.nav_to_module(session_browser, 'storage')
        assert _is_root_disk_shown(session_browser)


def _is_root_disk_shown(browser):
    table_cells = browser.find_by_tag('td')
    return any(cell.text.split('\n')[0] == '/' for cell in table_cells)
