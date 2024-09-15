# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for samba app.
"""

import random
import string
import subprocess
import urllib

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.samba]


class TestSambaApp(functional.BaseAppTests):
    app_name = 'samba'
    has_service = True
    has_web = False

    @pytest.fixture(scope='class', autouse=True)
    def fixture_setup(self, session_browser):
        """Setup the app."""
        functional.login(session_browser)
        functional.networks_set_firewall_zone(session_browser, 'internal')

    @pytest.mark.parametrize('share_type', ['open', 'group', 'home'])
    def test_enable_disable_samba_share(self, session_browser, share_type):
        """Test enabling and disabling Samba share."""
        _set_share(session_browser, share_type, status='enabled')

        _assert_share_is_writable(share_type)
        if share_type == 'open':
            _assert_share_is_writable(share_type, as_guest=True)
        else:
            _assert_share_is_not_accessible(share_type, as_guest=True)

        _set_share(session_browser, share_type, status='disabled')
        _assert_share_is_not_available(share_type)


def _set_share(browser, share_type, status='enabled'):
    """Enable or disable samba share."""
    disk_name = 'disk'
    share_row_id = 'samba-share-{0}-{1}'.format(disk_name, share_type)

    functional.nav_to_module(browser, 'samba')
    share = browser.find_by_id(share_row_id)
    share_btn = share.find_by_css('.share-status').find_by_tag('button').first

    if status == 'enabled' and share_btn['value'] == 'enable':
        share_btn.click()
    elif status == 'disabled' and share_btn['value'] == 'disable':
        share_btn.click()


def _write_to_share(share_type, as_guest=False):
    """Write to the samba share, return output messages as string."""
    disk_name = 'disk'
    default_url = functional.config['DEFAULT']['url']
    if share_type == 'open':
        share_name = disk_name
    else:
        share_name = '{0}_{1}'.format(disk_name, share_type)
    hostname = urllib.parse.urlparse(default_url).hostname
    servicename = '\\\\{0}\\{1}'.format(hostname, share_name)
    directory = '_plinth-test_{0}'.format(''.join(
        random.SystemRandom().choices(string.ascii_letters, k=8)))
    port = functional.config['DEFAULT']['samba_port']

    smb_command = ['smbclient', '-W', 'WORKGROUP', '-p', port]
    if as_guest:
        smb_command += ['-N']
    else:
        smb_command += [
            '-U', '{0}%{1}'.format(functional.config['DEFAULT']['username'],
                                   functional.config['DEFAULT']['password'])
        ]
    smb_command += [
        servicename, '-c', 'mkdir {0}; rmdir {0}'.format(directory)
    ]

    return subprocess.check_output(smb_command).decode()


def _assert_share_is_writable(share_type, as_guest=False):
    """Assert that samba share is writable."""
    output = _write_to_share(share_type, as_guest)

    assert not output, output


def _assert_share_is_not_accessible(share_type, as_guest=False):
    """Assert that samba share is not accessible."""
    try:
        _write_to_share(share_type, as_guest)
    except subprocess.CalledProcessError as err:
        err_output = err.output.decode()
        assert 'NT_STATUS_ACCESS_DENIED' in err_output, err_output
    else:
        assert False, 'Can access the share.'


def _assert_share_is_not_available(share_type):
    """Assert that samba share is not available."""
    try:
        _write_to_share(share_type)
    except subprocess.CalledProcessError as err:
        err_output = err.output.decode()
        assert 'NT_STATUS_BAD_NETWORK_NAME' in err_output, err_output
    else:
        assert False, 'Can access the share.'
