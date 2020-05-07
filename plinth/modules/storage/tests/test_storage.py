# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for storage module operations.
"""

import os
import re
import subprocess
import tempfile

import pytest


def _get_partition_device(device, partition_number):
    """Return the device corresponding to a partition in a given device."""
    if re.match('[0-9]', device[-1]):
        return device + 'p' + str(partition_number)

    return device + str(partition_number)


class Disk():
    """Context manager to create/destroy a disk."""

    def __init__(self, test_case, size, disk_info, file_system_info=None):
        """Initialize the context manager object."""
        self.size = size
        self.test_case = test_case
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

    def _setup_loopback(self):
        """Setup loop back on the create disk file."""
        command = 'losetup --show --find {file}'.format(
            file=self.disk_file.name)
        process = subprocess.run(command.split(), stdout=subprocess.PIPE,
                                 check=True)
        device = process.stdout.decode().strip()

        subprocess.run(['partprobe', device], check=True)

        self.device = device
        self.test_case.device = device

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
            device = _get_partition_device(self.device, partition)
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
            device = _get_partition_device(self.device, partition)
            subprocess.run(['umount', device], check=False)

    def _cleanup_loopback(self):
        """Undo the loopback device setup."""
        subprocess.run(['losetup', '--detach', self.device])

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

    def __exit__(self, *exc):
        """Exit the context, destroy the test disk."""
        self._unmount_file_systems()
        self._cleanup_loopback()
        self._remove_disk_file()


class TestActions:
    """Test all actions related to storage."""

    @pytest.mark.usefixtures('needs_root')
    def test_simple_case(self):
        """Test a simple with no complications"""
        disk_info = [
            'mktable msdos', 'mkpart primary btrfs 1 8',
            'mkpart primary btrfs 9 16', 'mkpart primary btrfs 20 200'
        ]
        with Disk(self, 256, disk_info, [(3, 'btrfs')]):
            # No free space
            self.assert_free_space(1, space=False)
            # < 10 MiB of free space
            self.assert_free_space(2, space=False)
            self.assert_free_space(3, space=True)

            self.expand_partition(1, success=False)
            self.expand_partition(2, success=False)
            self.expand_partition(3, success=True)
            self.expand_partition(3, success=False)

    @pytest.mark.usefixtures('needs_root')
    def test_extended_partition_free_space(self):
        """Test that free space does not show up when outside extended."""
        disk_info = [
            'mktable msdos', 'mkpart primary 1 8', 'mkpart extended 8 32',
            'mkpart logical 9 16'
        ]
        with Disk(self, 64, disk_info):
            self.assert_free_space(5, space=False)
            self.expand_partition(5, success=False)

    @pytest.mark.usefixtures('needs_root')
    def test_gpt_partition_free_space(self):
        """Test that GPT partitions can be expanded."""
        # Specifically check for partition number > 4
        disk_info = [
            'mktable gpt', 'mkpart primary 1 4', 'mkpart extended 4 8',
            'mkpart extended 8 12', 'mkpart extended 12 16',
            'mkpart extended 16 160'
        ]
        with Disk(self, 256, disk_info, [(5, 'btrfs')]):
            self.assert_free_space(5, space=True)
            self.expand_partition(5, success=True)
            self.expand_partition(5, success=False)

    @pytest.mark.usefixtures('needs_root')
    def test_unsupported_file_system(self):
        """Test that free space after unknown file system does not count."""
        disk_info = ['mktable msdos', 'mkpart primary 1 8']
        with Disk(self, 32, disk_info):
            self.assert_free_space(1, space=False)
            self.expand_partition(1, success=False)

    @pytest.mark.usefixtures('needs_root')
    def test_btrfs_expansion(self):
        """Test that btrfs file system can be expanded."""
        disk_info = ['mktable msdos', 'mkpart primary btrfs 1 200']
        with Disk(self, 256, disk_info, [(1, 'btrfs')]):
            self.expand_partition(1, success=True)
            self.expand_partition(1, success=False)
            self.assert_btrfs_file_system_healthy(1)

    @pytest.mark.usefixtures('needs_root')
    def test_ext4_expansion(self):
        """Test that ext4 file system can be expanded."""
        disk_info = ['mktable msdos', 'mkpart primary ext4 1 64']
        with Disk(self, 128, disk_info, [(1, 'ext4')]):
            self.expand_partition(1, success=True)
            self.expand_partition(1, success=False)
            self.assert_ext4_file_system_healthy(1)

    def assert_free_space(self, partition_number, space=True):
        """Verify that free is available/not available after a partition."""
        device = _get_partition_device(self.device, partition_number)
        result = self.check_action(
            ['storage', 'is-partition-expandable', device])
        assert result == space

    def expand_partition(self, partition_number, success=True):
        """Expand a partition."""
        self.assert_aligned(partition_number)
        device = _get_partition_device(self.device, partition_number)
        result = self.check_action(['storage', 'expand-partition', device])
        assert result == success
        self.assert_aligned(partition_number)

    @staticmethod
    def call_action(action_command, **kwargs):
        """Call the action script."""
        current_directory = os.path.dirname(os.path.realpath(__file__))
        action = os.path.join(current_directory, '..', '..', '..', '..',
                              'actions', action_command[0])
        action_command[0] = action
        kwargs['stdout'] = kwargs.get('stdout', subprocess.DEVNULL)
        kwargs['stderr'] = kwargs.get('stderr', subprocess.DEVNULL)
        kwargs['check'] = kwargs.get('check', True)
        return subprocess.run(action_command, **kwargs)

    def check_action(self, action_command):
        """Return success/failure result of the action command."""
        try:
            self.call_action(action_command)
            return True
        except subprocess.CalledProcessError:
            return False

    def assert_aligned(self, partition_number):
        """Test that partition is optimally aligned."""
        subprocess.run([
            'parted', '--script', self.device, 'align-check', 'opti',
            str(partition_number)
        ])

    def assert_btrfs_file_system_healthy(self, partition_number):
        """Perform a successful ext4 file system check."""
        device = _get_partition_device(self.device, partition_number)
        command = ['btrfs', 'check', '--force', device]
        subprocess.run(command, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)

    def assert_ext4_file_system_healthy(self, partition_number):
        """Perform a successful ext4 file system check."""
        device = _get_partition_device(self.device, partition_number)
        command = ['e2fsck', '-n', device]
        subprocess.run(command, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)

    def assert_validate_directory(self, path, error, check_writable=False,
                                  check_creatable=False):
        """Perform directory validation checks."""
        action_command = ['storage', 'validate-directory', '--path', path]
        if check_writable:
            action_command += ['--check-writable']
        if check_creatable:
            action_command += ['--check-creatable']
        proc = self.call_action(action_command, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        output = proc.stdout.decode()
        if 'ValidationError' in output:
            error_nr = output.strip().split()[1]
            assert error_nr == error
        else:
            assert output == error

    @pytest.mark.usefixtures('needs_not_root')
    @pytest.mark.parametrize('path,error', [('/missing', '1'),
                                            ('/etc/os-release', '2'),
                                            ('/root', '3'), ('/', ''),
                                            ('/etc/..', '')])
    def test_validate_directory(self, path, error):
        """Test that directory validation returns expected output."""
        self.assert_validate_directory(path, error)

    @pytest.mark.usefixtures('needs_not_root')
    @pytest.mark.parametrize('path,error', [('/', '4'), ('/tmp', '')])
    def test_validate_directory_writable(self, path, error):
        """Test that directory writable validation returns expected output."""
        self.assert_validate_directory(path, error, check_writable=True)

    @pytest.mark.usefixtures('needs_not_root')
    @pytest.mark.parametrize(
        'path,error', [('/var/lib/plinth_storage_test_not_exists', '4'),
                       ('/tmp/plint_storage_test_not_exists', ''),
                       ('/var/../tmp/plint_storage_test_not_exists', '')])
    def test_validate_directory_creatable(self, path, error):
        """Test that directory creatable validation returns expected output."""
        self.assert_validate_directory(path, error, check_creatable=True)
