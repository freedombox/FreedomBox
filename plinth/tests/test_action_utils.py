# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for key/value store.
"""

import json
import pathlib
import subprocess
from unittest.mock import Mock, call, patch

import pytest

from plinth.action_utils import (get_addresses, get_hostname,
                                 is_systemd_running, move_uploaded_file, run,
                                 run_as_user, service_action, service_disable,
                                 service_enable, service_is_enabled,
                                 service_is_running, service_reload,
                                 service_restart, service_start, service_stop,
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
    mock.assert_called_with(UNKNOWN, 'start', check=False)
    service_stop(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'stop', check=False)
    service_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'restart', check=False)
    service_try_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'try-restart', check=False)
    service_reload(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'reload', check=False)
    service_try_reload_or_restart(UNKNOWN)
    mock.assert_called_with(UNKNOWN, 'try-reload-or-restart', check=False)


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


@pytest.fixture(name='upload_dir')
def fixture_update_dir(tmp_path):
    """Patch Django file upload directory."""
    tmp_path /= 'source'
    tmp_path.mkdir()

    import plinth.settings
    old_value = plinth.settings.FILE_UPLOAD_TEMP_DIR
    plinth.settings.FILE_UPLOAD_TEMP_DIR = tmp_path
    yield tmp_path
    plinth.settings.FILE_UPLOAD_TEMP_DIR = old_value


def test_move_uploaded_file(tmp_path, upload_dir):
    """Test moving Django uploaded file to destination directory."""
    tmp_path /= 'destination'
    tmp_path.mkdir()

    # Source file does not exist
    source = tmp_path / 'does-non-exist'
    destination = tmp_path / 'destination'
    destination_file_name = 'destination-file-name'
    with pytest.raises(FileNotFoundError):
        move_uploaded_file(source, destination, destination_file_name)

    # Source is not a file
    source = tmp_path / 'source-dir'
    source.mkdir()
    with pytest.raises(ValueError, match='Source is not a file'):
        move_uploaded_file(source, destination, destination_file_name)

    # Source is not in expected temporary upload directory
    source = tmp_path / 'source-file'
    source.touch()
    with pytest.raises(
            ValueError,
            match='Uploaded file is not in expected temp directory'):
        move_uploaded_file(source, destination, destination_file_name)

    # Destination does not exist
    source = upload_dir / 'source-file'
    source.touch()
    with pytest.raises(ValueError, match='Destination is not a directory'):
        move_uploaded_file(source, destination, destination_file_name)

    # Destination is not a file
    destination.touch()
    with pytest.raises(ValueError, match='Destination is not a directory'):
        move_uploaded_file(source, destination, destination_file_name)

    # Destination file name is a multi-component path
    destination.unlink()
    destination.mkdir()
    destination_file_name = '../destination-file-name'
    with pytest.raises(ValueError, match='Invalid destination file name'):
        move_uploaded_file(source, destination, destination_file_name)

    # Destination file exists and override is not allowed
    destination_file_name = 'destination-file-exists'
    (destination / destination_file_name).touch()
    with pytest.raises(FileExistsError, match='Destination already exists'):
        move_uploaded_file(source, destination, destination_file_name)

    with pytest.raises(FileExistsError, match='Destination already exists'):
        move_uploaded_file(source, destination, destination_file_name,
                           allow_overwrite=False)

    # Successful move
    with patch('shutil.chown') as chown:
        destination_file = destination / destination_file_name
        destination_file.unlink()
        source.write_text('x-contents-1')
        move_uploaded_file(source, destination, destination_file_name)
        chown.mock_calls = [call(destination_file, 'root', 'root')]
        assert destination_file.stat().st_mode & 0o777 == 0o644
        assert destination_file.read_text() == 'x-contents-1'
        assert not source.exists()

        chown.reset_mock()
        source.write_text('x-contents-2')
        move_uploaded_file(source, destination, destination_file_name,
                           allow_overwrite=True, user='x-user',
                           group='x-group', permissions=0o600)
        chown.mock_calls = [call(destination_file, 'x-user', 'x-group')]
        assert destination_file.stat().st_mode & 0o777 == 0o600
        assert destination_file.read_text() == 'x-contents-2'
        assert not source.exists()


@patch('subprocess.run')
def test_run_as_user(subprocess_run):
    """Test running a command as another user works."""
    subprocess_run.return_value = 'test-return-value'
    return_value = run_as_user(['command', 'arg1', '--foo'],
                               username='foouser', stdout=subprocess.PIPE,
                               check=True)
    assert return_value == 'test-return-value'
    assert subprocess_run.mock_calls == [
        call(
            ['runuser', '--user', 'foouser', '--', 'command', 'arg1', '--foo'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    ]


@patch('plinth.actions.thread_storage')
@patch('subprocess.run')
def test_run_capture(subprocess_run, thread_storage):
    """Test running a command with stdin/stdout capture works."""
    thread_storage.stdout = 'initial-stdout'
    thread_storage.stderr = 'initial-stderr'

    subprocess_run.return_value = Mock()
    subprocess_run.return_value.stdout = 'test-stdout'
    subprocess_run.return_value.stderr = 'test-stderr'

    return_value = run(['command', 'arg1', '--foo'], check=True)
    assert return_value == subprocess_run.return_value
    assert subprocess_run.mock_calls == [
        call(['command', 'arg1', '--foo'], stdout=subprocess.PIPE,
             stderr=subprocess.PIPE, check=True)
    ]
    assert thread_storage.stdout == 'initial-stdouttest-stdout'
    assert thread_storage.stderr == 'initial-stderrtest-stderr'


@patch('plinth.actions.thread_storage')
@patch('subprocess.run')
def test_run_no_capture(subprocess_run, thread_storage):
    """Test running a command without stdin/stdout capture works."""
    thread_storage.stdout = 'initial-stdout'
    thread_storage.stderr = 'initial-stderr'

    subprocess_run.return_value = Mock()
    subprocess_run.return_value.stdout = 'test-stdout'
    subprocess_run.return_value.stderr = 'test-stderr'

    return_value = run(['command', 'arg1', '--foo'], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    assert return_value == subprocess_run.return_value
    assert subprocess_run.mock_calls == [
        call(['command', 'arg1', '--foo'], stdout=subprocess.PIPE,
             stderr=subprocess.PIPE, check=True)
    ]
    assert thread_storage.stdout == 'initial-stdout'
    assert thread_storage.stderr == 'initial-stderr'


@patch('plinth.actions.thread_storage', None)
@patch('subprocess.run')
def test_run_no_storage(subprocess_run):
    """Test running a command without thread storage."""
    subprocess_run.return_value = Mock()
    subprocess_run.return_value.stdout = 'test-stdout'
    subprocess_run.return_value.stderr = 'test-stderr'

    run(['command', 'arg1', '--foo'], check=True)
