# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for snapshot app.
"""

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('snapshot.feature')


@given('the list of snapshots is empty')
def empty_snapshots_list(session_browser):
    _delete_all(session_browser)
    return _get_count(session_browser)


@when('I manually create a snapshot')
def create_snapshot(session_browser):
    _create(session_browser)


@then(parsers.parse('there should be {count:d} more snapshots in the list'))
def verify_snapshot_count(session_browser, count, empty_snapshots_list):
    assert _get_count(session_browser) == count + empty_snapshots_list


@given(
    parsers.parse(
        'snapshots are configured with free space {free_space:d}, timeline '
        'snapshots {timeline_enabled:w}, software snapshots '
        '{software_enabled:w}, hourly limit {hourly:d}, daily limit {daily:d}'
        ', weekly limit {weekly:d}, monthly limit {monthly:d}, yearly limit '
        '{yearly:d}'))
def snapshot_given_set_configuration(session_browser, free_space,
                                     timeline_enabled, software_enabled,
                                     hourly, daily, weekly, monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    _set_configuration(session_browser, free_space, timeline_enabled,
                       software_enabled, hourly, daily, weekly, monthly,
                       yearly)


@when(
    parsers.parse(
        'I configure snapshots with free space {free_space:d}, '
        'timeline snapshots {timeline_enabled:w}, '
        'software snapshots {software_enabled:w}, hourly limit {hourly:d}, '
        'daily limit {daily:d}, weekly limit {weekly:d}, monthly limit '
        '{monthly:d}, yearly limit {yearly:d}'))
def snapshot_set_configuration(session_browser, free_space, timeline_enabled,
                               software_enabled, hourly, daily, weekly,
                               monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    _set_configuration(session_browser, free_space, timeline_enabled,
                       software_enabled, hourly, daily, weekly, monthly,
                       yearly)


@then(
    parsers.parse(
        'snapshots should be configured with free space {free_space:d}, '
        'timeline snapshots {timeline_enabled:w}, software snapshots '
        '{software_enabled:w}, hourly limit {hourly:d}, daily limit '
        '{daily:d}, weekly limit {weekly:d}, monthly limit {monthly:d}, '
        'yearly limit {yearly:d}'))
def snapshot_assert_configuration(session_browser, free_space,
                                  timeline_enabled, software_enabled, hourly,
                                  daily, weekly, monthly, yearly):
    timeline_enabled = (timeline_enabled == 'enabled')
    software_enabled = (software_enabled == 'enabled')
    assert (free_space, timeline_enabled, software_enabled, hourly, daily,
            weekly, monthly, yearly) == _get_configuration(session_browser)


def _delete_all(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    delete_button = browser.find_by_name('delete_selected').first
    if not delete_button['disabled']:
        browser.find_by_id('select-all').check()
        functional.submit(browser, delete_button)

        confirm_button = browser.find_by_name('delete_confirm')
        if confirm_button:  # Only if redirected to confirm page
            functional.submit(browser, confirm_button)


def _create(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    functional.submit(browser)  # Click on 'Create Snapshot'


def _get_count(browser):
    functional.visit(browser, '/plinth/sys/snapshot/manage/')
    # Subtract 1 for table header
    return len(browser.find_by_xpath('//tr')) - 1


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
    functional.submit(browser)


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
