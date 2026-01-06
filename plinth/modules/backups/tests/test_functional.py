# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for backups app.
"""

import os
import tempfile
import time
import urllib.parse

import pytest
import requests

from plinth.tests import functional

pytestmark = [pytest.mark.system, pytest.mark.backups]

REMOTE_PATH = 'tester@localhost:~/backups'


@pytest.fixture(scope='module', autouse=True)
def fixture_background(session_browser):
    """Login and install the app."""
    functional.login(session_browser)
    functional.install(session_browser, 'bind')
    functional.app_enable(session_browser, 'bind')
    yield
    functional.app_disable(session_browser, 'bind')
    _backup_schedule_disable(session_browser)


@pytest.fixture(scope='session')
def downloaded_file_info():
    return dict()


def test_browser_waits_after_restore(session_browser):
    """Test that browser waits for redirect after restoring a backup."""
    functional.backup_create(session_browser, 'bind', 'test_backups')
    functional.backup_restore(session_browser, 'bind', 'test_backups')

    _open_main_page(session_browser)
    time.sleep(5)
    _assert_main_page_is_shown(session_browser)


def test_download_upload_restore(session_browser, downloaded_file_info):
    """Test download, upload, and restore a backup."""
    functional.set_forwarders(session_browser, '1.1.1.1')
    functional.backup_create(session_browser, 'bind', 'test_backups')

    functional.set_forwarders(session_browser, '1.0.0.1')
    _backup_download(session_browser, downloaded_file_info, 'test_backups')
    _backup_restore_from_upload(session_browser, 'bind', downloaded_file_info)

    assert functional.get_forwarders(session_browser) == '1.1.1.1'


def test_set_schedule(session_browser):
    """Test set a schedule for a repository."""
    _backup_schedule_set(session_browser, enable=False, daily=1, weekly=2,
                         monthly=3, run_at=2, without_app='names')

    _backup_schedule_set(session_browser, enable=True, daily=10, weekly=20,
                         monthly=30, run_at=15, without_app='firewall')

    _backup_schedule_assert(session_browser, enable=True, daily=10, weekly=20,
                            monthly=30, run_at=15, without_app='firewall')


def test_remote_backup_location(session_browser):
    """Test remote backup location operations."""
    _add_remote_backup_location(session_browser)
    assert _has_remote_backup_location(session_browser)

    _remove_remote_backup_location(session_browser)
    assert not _has_remote_backup_location(session_browser)

    # Add it again without providing SSH password.
    _add_remote_backup_location(session_browser, False)
    assert _has_remote_backup_location(session_browser)

    _remove_remote_backup_location(session_browser)
    assert not _has_remote_backup_location(session_browser)


def _assert_main_page_is_shown(session_browser):
    assert (session_browser.url.endswith('/plinth/'))


def _backup_download(session_browser, downloaded_file_info, archive_name):
    file_path = _download(session_browser, archive_name)
    downloaded_file_info['path'] = file_path


def _backup_restore_from_upload(session_browser, app_name,
                                downloaded_file_info):
    path = downloaded_file_info['path']
    try:
        _upload_and_restore(session_browser, app_name, path)
    except Exception as err:
        raise err
    finally:
        os.remove(path)


def _backup_schedule_assert(session_browser, enable, daily, weekly, monthly,
                            run_at, without_app):
    schedule = _backup_schedule_get(session_browser)
    assert schedule['enable'] == enable
    assert schedule['daily'] == daily
    assert schedule['weekly'] == weekly
    assert schedule['monthly'] == monthly
    assert schedule['run_at'] == run_at
    assert len(schedule['without_apps']) == 1
    assert schedule['without_apps'][0] == without_app


def _backup_schedule_disable(session_browser):
    """Disable schedule for the root repository."""
    _backup_schedule_set(session_browser, False, 1, 2, 3, 2, 'names')


def _backup_schedule_get(browser):
    """Return the current schedule set for the root repository."""
    functional.nav_to_module(browser, 'backups')
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href(
            '/plinth/sys/backups/root/schedule/').first.click()

    without_apps = []
    elements = browser.find_by_name('backups_schedule-selected_apps')
    for element in elements:
        if not element.checked:
            without_apps.append(element.value)

    return {
        'enable':
            browser.find_by_name('backups_schedule-enabled').checked,
        'daily':
            int(browser.find_by_name('backups_schedule-daily_to_keep').value),
        'weekly':
            int(browser.find_by_name('backups_schedule-weekly_to_keep').value),
        'monthly':
            int(
                browser.find_by_name('backups_schedule-monthly_to_keep').value
            ),
        'run_at':
            int(browser.find_by_name('backups_schedule-run_at_hour').value),
        'without_apps':
            without_apps
    }


def _backup_schedule_set(browser, enable, daily, weekly, monthly, run_at,
                         without_app):
    """Set the schedule for root repository."""
    functional.nav_to_module(browser, 'backups')
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href(
            '/plinth/sys/backups/root/schedule/').first.click()

    if enable:
        browser.find_by_name('backups_schedule-enabled').check()
    else:
        browser.find_by_name('backups_schedule-enabled').uncheck()

    browser.fill('backups_schedule-daily_to_keep', daily)
    browser.fill('backups_schedule-weekly_to_keep', weekly)
    browser.fill('backups_schedule-monthly_to_keep', monthly)
    browser.fill('backups_schedule-run_at_hour', run_at)
    functional.eventually(browser.find_by_css, args=['.select-all'])
    browser.find_by_css('.select-all').first.check()
    browser.find_by_css(f'input[value="{without_app}"]').first.uncheck()
    functional.submit(browser, form_class='form-backups_schedule')


def _download_file_logged_in(browser, url, suffix=''):
    """Download a file from Plinth, pretend being logged in via cookies"""
    if not url.startswith('http'):
        current_url = urllib.parse.urlparse(browser.url)
        url = '%s://%s%s' % (current_url.scheme, current_url.netloc, url)
    cookies = browser.driver.get_cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in cookies}
    response = requests.get(url, verify=False, cookies=cookies)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        for chunk in response.iter_content(chunk_size=128):
            temp_file.write(chunk)
    return temp_file.name


def _download(browser, archive_name=None):
    functional.nav_to_module(browser, 'backups')
    href = f'/plinth/sys/backups/root/download/{archive_name}/'
    url = functional.base_url + href
    file_path = _download_file_logged_in(browser, url, suffix='.tar.gz')
    return file_path


def _open_main_page(browser):
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href('/plinth/').first.click()


def _upload_and_restore(browser, app_name, downloaded_file_path):
    functional.nav_to_module(browser, 'backups')
    with functional.wait_for_page_update(browser):
        browser.links.find_by_href('/plinth/sys/backups/upload/').first.click()

    fileinput = browser.find_by_id('id_backups-file')
    fileinput.fill(downloaded_file_path)
    # submit upload form
    functional.submit(browser, form_class='form-upload')
    # submit restore form
    with functional.wait_for_page_update(browser,
                                         expected_url='/plinth/sys/backups/'):
        functional.submit(browser, form_class='form-restore')


def _has_remote_backup_location(browser) -> bool:
    functional.nav_to_module(browser, 'backups')
    return browser.is_text_present(REMOTE_PATH)


def _add_remote_backup_location(browser, ssh_use_password=True):
    if _has_remote_backup_location(browser):
        _remove_remote_backup_location(browser)

    browser.links.find_by_href(
        '/plinth/sys/backups/repositories/add-remote/').first.click()
    browser.find_by_name('repository').fill(REMOTE_PATH)
    password = functional.get_password(
        functional.config['DEFAULT']['username'])
    if ssh_use_password:
        browser.find_by_id('id_ssh_auth_type_password').first.check()
        browser.find_by_name('ssh_password').fill(password)
    else:
        browser.find_by_id('id_ssh_auth_type_key').first.check()

    browser.choose('id_encryption', 'repokey')
    browser.find_by_name('encryption_passphrase').fill(password)
    browser.find_by_name('confirm_encryption_passphrase').fill(password)
    submit_button = browser.find_by_value('Create Location')
    functional.submit(browser, element=submit_button)

    assert browser.is_text_present('Added new remote SSH repository.')

    if 'ssh-verify' in browser.url:
        _verify_host_key(browser)


def _remove_remote_backup_location(browser):
    remote_locations = browser.find_by_tag('table')[1]
    remote_locations.links.find_by_partial_href('/delete/').first.click()

    submit_button = browser.find_by_value('Remove Location')
    functional.submit(browser, element=submit_button)


def _verify_host_key(browser):
    browser.find_by_name('ssh_public_key').first.click()
    submit_button = browser.find_by_value('Verify Host')
    functional.submit(browser, element=submit_button)
    assert browser.is_text_present('SSH host verified.')
