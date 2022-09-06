# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for snapshot app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.snapshot]


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'snapshot')
    if not _is_snapshot_supported(session_browser):
        pytest.skip('Filesystem doesn\'t support snapshots')


def test_create(session_browser):
    """Test creating a snapshot."""
    _empty_snapshots_list(session_browser)
    _create_snapshot(session_browser)
    assert _get_count(session_browser) == 1


def test_configure(session_browser):
    """Test configuring snapshots."""
    _set_configuration(session_browser, free_space=30, timeline_enabled=False,
                       software_enabled=False, hourly=10, daily=3, weekly=2,
                       monthly=2, yearly=0)
    _set_configuration(session_browser, free_space=20, timeline_enabled=True,
                       software_enabled=True, hourly=3, daily=2, weekly=1,
                       monthly=1, yearly=1)
    assert _get_configuration(session_browser) == (20, True, True, 3, 2, 1, 1,
                                                   1)


@pytest.mark.backups
def test_backup_restore(session_browser):
    """Test backup and restore of configuration."""
    _set_configuration(session_browser, free_space=30, timeline_enabled=False,
                       software_enabled=False, hourly=10, daily=3, weekly=2,
                       monthly=2, yearly=0)
    functional.backup_create(session_browser, 'snapshot', 'test_snapshot')

    _set_configuration(session_browser, free_space=20, timeline_enabled=True,
                       software_enabled=True, hourly=3, daily=2, weekly=1,
                       monthly=1, yearly=1)
    functional.backup_restore(session_browser, 'snapshot', 'test_snapshot')

    assert _get_configuration(session_browser) == (30, False, False, 10, 3, 2,
                                                   2, 0)


def _empty_snapshots_list(browser):
    _delete_all(browser)
    return _get_count(browser)


def _delete_all(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    delete_button = browser.find_by_name('delete_selected').first
    if not delete_button['disabled']:
        browser.find_by_id('select-all').check()
        functional.submit(browser, delete_button)

        confirm_button = browser.find_by_name('delete_confirm')
        if confirm_button:  # Only if redirected to confirm page
            functional.submit(browser, confirm_button)


def _create_snapshot(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    create_button = browser.find_by_name('create').first
    functional.submit(browser, create_button)


def _get_count(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    # Subtract 1 for table header
    return len(browser.find_by_xpath('//tr')) - 1


def _is_snapshot_supported(browser):
    """Return whether the filesystem supports snapshots."""
    functional.nav_to_module(browser, 'snapshot')
    return not bool(browser.find_by_id('snapshot-not-supported'))


def _set_configuration(browser, free_space, timeline_enabled, software_enabled,
                       hourly, daily, weekly, monthly, yearly):
    """Set the configuration for snapshots."""
    functional.nav_to_module(browser, 'snapshot')
    browser.find_by_name('free_space').select(free_space / 100)
    browser.find_by_name('enable_timeline_snapshots').select(
        'yes' if timeline_enabled else 'no')
    browser.find_by_name('enable_software_snapshots').select(
        'yes' if software_enabled else 'no')
    browser.find_by_name('hourly_limit').fill(hourly)
    browser.find_by_name('daily_limit').fill(daily)
    browser.find_by_name('weekly_limit').fill(weekly)
    browser.find_by_name('monthly_limit').fill(monthly)
    browser.find_by_name('yearly_limit').fill(yearly)
    functional.submit(browser, form_class='form-configuration')


def _get_configuration(browser):
    """Return the current configuration for snapshots."""
    functional.nav_to_module(browser, 'snapshot')
    return (int(float(browser.find_by_name('free_space').value) * 100),
            browser.find_by_name('enable_timeline_snapshots').value == 'yes',
            browser.find_by_name('enable_software_snapshots').value == 'yes',
            int(browser.find_by_name('hourly_limit').value),
            int(browser.find_by_name('daily_limit').value),
            int(browser.find_by_name('weekly_limit').value),
            int(browser.find_by_name('monthly_limit').value),
            int(browser.find_by_name('yearly_limit').value))
