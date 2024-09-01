# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for storage module operations.
"""

import contextlib
import dataclasses
import re
import subprocess
import tempfile
from unittest.mock import patch

import psutil
import pytest
from django.utils.translation import gettext_noop

from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules import storage
from plinth.modules.storage import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.storage.privileged']


class Disk():
    """Context manager to create/destroy a disk."""

    def __init__(self, size, disk_info, file_system_info=None):
        """Initialize the context manager object."""
        self.size = size
        self.disk_info = disk_info
        self.file_system_info = file_system_info

        self.disk_file = None
        self.device = None

    def _create_disk_file(self):
        """Create a temporary file to act as a disk."""
        disk_file = tempfile.NamedTemporaryFile()

        command = 'dd if=/dev/zero of={file} bs=1M count={size}' \
                  .format(size=self.size, file=disk_file.name)
        subprocess.run(command.split(), stderr=subprocess.DEVNULL, check=True)

        self.disk_file = disk_file

    def expand_disk_file(self, size):
        """Expand the disk file."""
        command = f'truncate --size={size}M {self.disk_file.name}'
        subprocess.run(command.split(), check=True)
        self._unmount_file_systems()
        self._cleanup_loopback()
        self._setup_loopback()

    def get_partition_device(self, partition_number):
        """Return the device corresponding to a partition in a given device."""
        if re.match('[0-9]', self.device[-1]):
            return self.device + 'p' + str(partition_number)

        return self.device + str(partition_number)

    @contextlib.contextmanager
    def mount_partition(self, partition_number):
        """Mount partition onto a directory if device has a filesystem."""
        device = self.get_partition_device(partition_number)
        if not self.file_system_info or \
           partition_number not in dict(self.file_system_info):
            yield '/'
            return

        with tempfile.TemporaryDirectory() as mount_path:
            subprocess.run(['mount', device, mount_path], check=True)
            try:
                yield mount_path
            finally:
                subprocess.run(['umount', mount_path], check=True)

    def _setup_loopback(self):
        """Setup loop back on the create disk file."""
        command = 'losetup --show --find {file}'.format(
            file=self.disk_file.name)
        process = subprocess.run(command.split(), stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, check=False)
        if process.returncode:
            if b'cannot find an unused loop device' in process.stderr:
                pytest.skip('Loopback devices not available')
            else:
                raise Exception(process.stderr)

        device = process.stdout.decode().strip()

        subprocess.run(['partprobe', device], check=True)

        self.device = device

    def _create_partitions(self):
        """Create partitions as specified in disk_info."""
        steps = [step.split() for step in self.disk_info]
        command = [
            'parted', '--align=optimal', '--script', self.disk_file.name
        ]
        for step in steps:
            command += step

        subprocess.run(command, check=True)

    def _create_file_systems(self):
        """Create file systems inside partitions."""
        if not self.file_system_info:
            return

        for partition, file_system_type in self.file_system_info:
            device = self.get_partition_device(partition)
            if file_system_type == 'btrfs':
                command = ['mkfs.btrfs', '-K', device]
            else:
                command = ['mkfs.ext4', device]

            subprocess.run(command, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=True)

    def _unmount_file_systems(self):
        """Unmount al partitions if it is mounted by external party."""
        if not self.file_system_info:
            return

        for partition, _ in self.file_system_info:
            device = self.get_partition_device(partition)
            subprocess.run(['umount', device], check=False)

    def _cleanup_loopback(self):
        """Undo the loopback device setup."""
        subprocess.run(['losetup', '--detach', self.device], check=False)

    def _remove_disk_file(self):
        """Delete the disk_file."""
        self.disk_file.close()
        self.disk_file = None

    def __enter__(self):
        """Enter the context, create the test disk."""
        self._create_disk_file()
        self._create_partitions()
        self._setup_loopback()
        self._create_file_systems()
        return self

    def __exit__(self, *exc):
        """Exit the context, destroy the test disk."""
        self._unmount_file_systems()
        self._cleanup_loopback()
        self._remove_disk_file()


def disk_space_available():
    """Return disk space available in temporary directory."""
    directory = tempfile.gettempdir()
    output = subprocess.check_output(['df', '-m', '--output=avail',
                                      directory]).decode()
    return int(output.splitlines()[1])


@pytest.mark.usefixtures('needs_root')
@pytest.mark.skipif(disk_space_available() < 1024,
                    reason='Needs 1024MiB of space')
def test_simple_case():
    """Test a simple with no complications"""
    disk_info = [
        'mktable msdos', 'mkpart primary btrfs 1 300',
        'mkpart primary btrfs 301 600', 'mkpart primary btrfs 608 900'
    ]
    # Btrfs volumes < 256 MiB can't be resized.
    # https://bugzilla.kernel.org/show_bug.cgi?id=118111
    with Disk(1024, disk_info, [(1, 'btrfs'), (2, 'btrfs'),
                                (3, 'btrfs')]) as disk:
        # No free space
        _assert_free_space(disk, 1, space=False)
        # < 10 MiB of free space
        _assert_free_space(disk, 2, space=False)
        _assert_free_space(disk, 3, space=True)

        _expand_partition(disk, 1, success=False)
        _expand_partition(disk, 2, success=False)
        _expand_partition(disk, 3, success=True)
        _expand_partition(disk, 3, success=False)


@pytest.mark.usefixtures('needs_root')
@pytest.mark.skipif(disk_space_available() < 512,
                    reason='Needs 512MiB of space')
def test_extended_partition_free_space():
    """Test that free space does not show up when outside extended."""
    disk_info = [
        'mktable msdos', 'mkpart primary 1 8', 'mkpart extended 8 500',
        'mkpart logical btrfs 9 300'
    ]
    with Disk(512, disk_info, [(5, 'btrfs')]) as disk:
        _assert_free_space(disk, 5, space=False)
        _expand_partition(disk, 5, success=False)


@pytest.mark.usefixtures('needs_root')
@pytest.mark.skipif(disk_space_available() < 512,
                    reason='Needs 512MiB of space')
def test_gpt_partition_free_space():
    """Test that GPT partitions can be expanded."""
    # Specifically check for partition number > 4
    disk_info = [
        'mktable gpt', 'mkpart primary 1 4', 'mkpart extended 4 8',
        'mkpart extended 8 12', 'mkpart extended 12 16',
        'mkpart extended 16 300'
    ]
    with Disk(512, disk_info, [(5, 'btrfs')]) as disk:
        # Second header already at the end
        _assert_free_space(disk, 5, space=True)
        _expand_partition(disk, 5, success=True)
        _expand_partition(disk, 5, success=False)
        disk.expand_disk_file(1024)
        # Second header not at the end
        _assert_free_space(disk, 5, space=True)
        _expand_partition(disk, 5, success=True)
        _expand_partition(disk, 5, success=False)


@pytest.mark.usefixtures('needs_root')
@pytest.mark.parametrize('partition_table_type', ['gpt', 'msdos'])
@pytest.mark.skipif(disk_space_available() < 32, reason='Needs 32MiB of space')
def test_unsupported_file_system(partition_table_type):
    """Test that free space after unknown file system does not count."""
    disk_info = [f'mktable {partition_table_type}', 'mkpart primary 1 8']
    with Disk(32, disk_info) as disk:
        _assert_free_space(disk, 1, space=False)
        _expand_partition(disk, 1, success=False)


@pytest.mark.usefixtures('needs_root')
@pytest.mark.parametrize('partition_table_type', ['gpt', 'msdos'])
@pytest.mark.skipif(disk_space_available() < 512,
                    reason='Needs 512MiB of space')
def test_btrfs_expansion(partition_table_type):
    """Test that btrfs file system can be expanded."""
    disk_info = [
        f'mktable {partition_table_type}', 'mkpart primary btrfs 1 300'
    ]
    with Disk(512, disk_info, [(1, 'btrfs')]) as disk:
        _expand_partition(disk, 1, success=True)
        _expand_partition(disk, 1, success=False)
        _assert_btrfs_file_system_healthy(disk, 1)


@pytest.mark.usefixtures('needs_root')
@pytest.mark.parametrize('partition_table_type', ['gpt', 'msdos'])
@pytest.mark.skipif(disk_space_available() < 128,
                    reason='Needs 128MiB of space')
def test_ext4_expansion(partition_table_type):
    """Test that ext4 file system can be expanded."""
    disk_info = [f'mktable {partition_table_type}', 'mkpart primary ext4 1 64']
    with Disk(128, disk_info, [(1, 'ext4')]) as disk:
        _expand_partition(disk, 1, success=True)
        _expand_partition(disk, 1, success=False)
        _assert_ext4_file_system_healthy(disk, 1)


def _assert_free_space(disk, partition_number, space=True):
    """Verify that free is available/not available after a partition."""
    device = disk.get_partition_device(partition_number)
    if space:
        privileged.is_partition_expandable(device)
    else:
        with pytest.raises(RuntimeError):
            privileged.is_partition_expandable(device)


def _expand_partition(disk, partition_number, success=True):
    """Expand a partition."""
    _assert_aligned(disk, partition_number)
    with disk.mount_partition(partition_number) as mount_point:
        device = disk.get_partition_device(partition_number)
        if success:
            privileged.expand_partition(device, mount_point)
        else:
            with pytest.raises(RuntimeError):
                privileged.expand_partition(device, mount_point)

    _assert_aligned(disk, partition_number)


def _assert_aligned(disk, partition_number):
    """Test that partition is optimally aligned."""
    subprocess.run([
        'parted', '--script', disk.device, 'align-check', 'opti',
        str(partition_number)
    ], check=True)


def _assert_btrfs_file_system_healthy(disk, partition_number):
    """Perform a successful ext4 file system check."""
    device = disk.get_partition_device(partition_number)
    command = ['btrfs', 'check', '--force', device]
    subprocess.run(command, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)


def _assert_ext4_file_system_healthy(disk, partition_number):
    """Perform a successful ext4 file system check."""
    device = disk.get_partition_device(partition_number)
    command = ['e2fsck', '-n', device]
    subprocess.run(command, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)


def _assert_validate_directory(path, error, check_writable=False,
                               check_creatable=False):
    """Perform directory validation checks."""
    if error:
        match = None if not error.args else error.args[0]
        with pytest.raises(error.__class__, match=match):
            privileged.validate_directory(path, check_creatable,
                                          check_writable)
    else:
        privileged.validate_directory(path, check_creatable, check_writable)


@pytest.mark.usefixtures('needs_not_root')
@pytest.mark.parametrize('path,error',
                         [('/missing', FileNotFoundError()),
                          ('/etc/os-release', NotADirectoryError()),
                          ('/root', PermissionError('read')), ('/', None),
                          ('/etc/..', None)])
def test_validate_directory(path, error):
    """Test that directory validation returns expected output."""
    _assert_validate_directory(path, error)


@pytest.mark.usefixtures('needs_not_root')
@pytest.mark.parametrize('path,error', [('/', PermissionError('write')),
                                        ('/tmp', None)])
def test_validate_directory_writable(path, error):
    """Test that directory writable validation returns expected output."""
    _assert_validate_directory(path, error, check_writable=True)


@pytest.mark.usefixtures('needs_not_root')
@pytest.mark.parametrize(
    'path,error',
    [('/var/lib/plinth_storage_test_not_exists', PermissionError('write')),
     ('/tmp/plint_storage_test_not_exists', None),
     ('/var/../tmp/plint_storage_test_not_exists', None)])
def test_validate_directory_creatable(path, error):
    """Test that directory creatable validation returns expected output."""
    _assert_validate_directory(path, error, check_creatable=True)


@patch('psutil.disk_partitions')
def test_is_partition_read_only(disk_partitions):
    """Test whether checking for ro partition works."""
    partition = psutil._common.sdiskpart  # pylint: disable=protected-access
    disk_partitions.return_value = [
        partition('/dev/root', '/', 'btrfs', 'rw,nosuid', 42, 42),
        partition('/dev/root', '/foo', 'btrfs', 'rw', 321, 321),
        partition('/dev/foo', '/bar', 'extfs', 'ro', 123, 123)
    ]
    assert not storage.is_partition_read_only('/')
    assert not storage.is_partition_read_only('/foo')
    assert storage.is_partition_read_only('/bar')


@patch('subprocess.check_output')
def test_diagnose_grub_configured(check_output):
    """Test whether checking grub-pc package configuration failed works."""
    diagnose = storage._diagnose_grub_configured \
        # pylint: disable=protected-access

    passed = DiagnosticCheck('storage-grub-configured',
                             gettext_noop('grub package is configured'),
                             Result.PASSED)
    failed = dataclasses.replace(passed, result=Result.FAILED)
    warning = dataclasses.replace(passed, result=Result.WARNING)

    # installed and configured
    check_output.return_value = b'ii '
    assert diagnose() == passed

    # failed configuration
    check_output.return_value = b'iF '
    assert diagnose() == failed

    # should be installed, but somehow is not
    check_output.return_value = b'in '
    assert diagnose() == warning

    # not installed
    check_output.return_value = b'un '
    assert diagnose() is None

    # grub-pc package is not available (e.g. ARM devices)
    check_output.side_effect = subprocess.CalledProcessError(
        cmd=[
            'dpkg-query', '--show', '--showformat=${db:Status-Abbrev}',
            'grub-pc'
        ], returncode=1,
        stderr=b'dpkg-query: no packages found matching grub-pc\n')
    assert diagnose() is None
