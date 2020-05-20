# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for samba app.
"""

import random
import string
import subprocess
import urllib

from pytest_bdd import parsers, scenarios, then, when

from plinth.tests import functional

scenarios('samba.feature')


@when(parsers.parse('I {task:w} the {share_type:w} samba share'))
def samba_enable_share(session_browser, task, share_type):
    if task == 'enable':
        _set_share(session_browser, share_type, status='enabled')
    elif task == 'disable':
        _set_share(session_browser, share_type, status='disabled')


@then(parsers.parse('I can write to the {share_type:w} samba share'))
def samba_share_should_be_writable(share_type):
    _assert_share_is_writable(share_type)


@then(parsers.parse('a guest user can write to the {share_type:w} samba share')
      )
def samba_share_should_be_writable_to_guest(share_type):
    _assert_share_is_writable(share_type, as_guest=True)


@then(
    parsers.parse('a guest user can\'t access the {share_type:w} samba share'))
def samba_share_should_not_be_accessible_to_guest(share_type):
    _assert_share_is_not_accessible(share_type, as_guest=True)


@then(parsers.parse('the {share_type:w} samba share should not be available'))
def samba_share_should_not_be_available(share_type):
    _assert_share_is_not_available(share_type)


def _set_share(browser, share_type, status='enabled'):
    """Enable or disable samba share."""
    disk_name = 'disk'
    share_type_name = '{0}_share'.format(share_type)
    functional.nav_to_module(browser, 'samba')
    for elem in browser.find_by_tag('td'):
        if elem.text == disk_name:
            share_form = elem.find_by_xpath('(..//*)[2]/form').first
            share_btn = share_form.find_by_name(share_type_name).first
            if status == 'enabled' and share_btn['value'] == 'enable':
                share_btn.click()
            elif status == 'disabled' and share_btn['value'] == 'disable':
                share_btn.click()
            break


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
    output = _write_to_share(share_type, as_guest=False)

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
    """Assert that samba share is not accessible."""
    try:
        _write_to_share(share_type)
    except subprocess.CalledProcessError as err:
        err_output = err.output.decode()
        assert 'NT_STATUS_BAD_NETWORK_NAME' in err_output, err_output
    else:
        assert False, 'Can access the share.'
