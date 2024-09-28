# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for key/value store.
"""

import json
import pathlib
import subprocess
from unittest.mock import patch

import pytest

from plinth.action_utils import (get_addresses, get_hostname,
                                 is_systemd_running, service_action,
                                 service_disable, service_enable,
                                 service_is_enabled, service_is_running,
                                 service_reload, service_restart,
                                 service_start, service_stop,
                                 service_try_reload_or_restart,
                                 service_try_restart, service_unmask)

UNKNOWN = 'unknowndeamon'

systemctl_path = pathlib.Path('/usr/bin/systemctl')
systemd_installed = pytest.mark.skipif(not systemctl_path.exists(),
                                       reason='systemd not available')

ip_path = pathlib.Path('/usr/bin/ip')
ip_installed = pytest.mark.skipif(not ip_path.exists(),
                                  reason='ip command not available')


@patch('os.path.exists')
def test_is_systemd_running(mock):
    """Trivial white box test for a trivial implementation."""
    mock.return_value = True
    assert is_systemd_running()
    mock.return_value = False
    assert not is_systemd_running()


@systemd_installed
def test_service_checks():
    """Test basic checks on status of an arbitrary service."""
    assert not service_is_running(UNKNOWN)
    assert not service_is_enabled(UNKNOWN)

    # expected is best if: generic. Alternatives: systemd-sysctl, logrotate
    expected = 'networking'
    if not service_is_running(expected):
        pytest.skip(f'Needs service {expected} running.')

    assert service_is_enabled(expected)


@pytest.mark.usefixtures('needs_root')
@systemd_installed
def test_service_enable_and_disable():
    """Test enabling and disabling of an arbitrary service."""
    # service is best if: non-essential part of FreedomBox that restarts fast
    service = 'unattended-upgrades'
    if not service_is_enabled(service):
        reason = f'Needs service {service} enabled.'
        pytest.skip(reason)

    service_disable(service)
    assert not service_is_running(service)
    service_enable(service)
    assert service_is_running(service)

    # Ignore unknown services, don't fail:
    service_disable(UNKNOWN)
    service_enable(UNKNOWN)


@patch('plinth.action_utils.service_action')
@systemd_installed
def test_service_actions(mock):
    """Trivial white box test for trivial implementations."""
    service_start(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'start')
    service_stop(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'stop')
    service_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'restart')
    service_try_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'try-restart')
    service_reload(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'reload')
    service_try_reload_or_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'try-reload-or-restart')


@pytest.mark.usefixtures('needs_root')
@systemd_installed
def test_service_unmask():
    """Test unmasking of an arbitrary masked service."""

    def is_masked(service):
        process = subprocess.run([
            'systemctl', 'list-unit-files', '--output=json',
            service + '.service'
        ], stdout=subprocess.PIPE, check=False)
        output = json.loads(process.stdout)
        return output[0]['state'] == 'masked' if output else False

    # SERVICE is best if: part of FreedomBox, so we can mess with least risk.
    service = 'samba-ad-dc'
    if not is_masked(service):
        pytest.skip(f'Needs service {service} masked.')

    service_unmask(service)
    assert not is_masked(service)

    service_action(service, 'mask')
    assert is_masked(service)


def test_get_hostname():
    """get_hostname returns a string.

    In fact, the maximum length for a hostname is 253 characters, but
    anything longer than 80 is very suspicious, so we fail the test.

    To avoid error messages pass as hostnames we seek and fail if we find
    some unexpected characters.
    """
    hostname = get_hostname()
    assert hostname
    assert isinstance(hostname, str)
    assert len(hostname) < 80
    for char in ' ,:;!?=$%&@*+()[]{}<>"\'':
        assert char not in hostname


@ip_installed
def test_get_addresses():
    """Test that any FreedomBox has some addresses."""
    ips = get_addresses()
    assert len(ips) > 3  # min: ip, 2x'localhost', hostname
    for address in ips:
        assert address['kind'] in ('4', '6')
