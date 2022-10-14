# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure disks manager."""

import os
import re
import stat
import subprocess

from plinth import utils
from plinth.actions import privileged


@privileged
def is_partition_expandable(device: str) -> int:
    """Return a list of partitions that can be expanded."""
    _, _, free_space = _get_free_space(device)
    return int(free_space['size'])


@privileged
def expand_partition(device: str, mount_point: str = '/'):
    """Expand a partition to take adjacent free space."""
    device, requested_partition, free_space = _get_free_space(device)

    if requested_partition['table_type'] == 'msdos' and \
       int(requested_partition['number']) >= 5:
        raise RuntimeError(
            'Expanding logical partitions currently unsupported')

    if requested_partition['table_type'] == 'gpt':
        _move_gpt_second_header(device)

    _resize_partition(device, requested_partition, free_space)
    _resize_file_system(device, requested_partition, free_space, mount_point)


def _move_gpt_second_header(device):
    """Move second header to the end of the disk.

    GPT scheme has two mostly identical partition table headers. One at the
    beginning of the disk and one at the end. When an image is written to
    larger disk, the second header is not at the end of the disk. Fix that by
    moving second partition to end of the disk before attempting partition
    resize.

    """
    command = ['sgdisk', '--move-second-header', device]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError('Error moving GPT second header to the end')


def _resize_partition(device, requested_partition, free_space):
    """Resize the partition table entry."""
    command = [
        'parted', '--align=optimal', '--script', device, 'unit', 'B',
        'resizepart', requested_partition['number'],
        str(free_space['end'])
    ]
    # XXX: Remove workaround after bug in parted is fixed:
    # https://debbugs.gnu.org/cgi/bugreport.cgi?bug=24215
    fallback_command = [
        'parted', '--align=optimal', device, '---pretend-input-tty', 'unit',
        'B', 'resizepart', requested_partition['number']
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        try:
            input_text = 'yes\n' + str(free_space['end'])
            subprocess.run(fallback_command, check=True,
                           input=input_text.encode())
        except subprocess.CalledProcessError as exception:
            raise RuntimeError(f'Error expanding partition: {exception}')


def _resize_file_system(device, requested_partition, free_space,
                        mount_point='/'):
    """Resize a file system inside a partition."""
    if requested_partition['type'] == 'btrfs':
        _resize_btrfs(device, requested_partition, free_space, mount_point)
    elif requested_partition['type'] == 'ext4':
        _resize_ext4(device, requested_partition, free_space, mount_point)


def _resize_ext4(device, requested_partition, _free_space, _mount_point):
    """Resize an ext4 file system inside a partition."""
    partition_device = _get_partition_device(device,
                                             requested_partition['number'])
    try:
        command = ['resize2fs', partition_device]
        subprocess.run(command, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as exception:
        raise RuntimeError(f'Error expanding filesystem: {exception}')


def _resize_btrfs(_device, _requested_partition, _free_space, mount_point='/'):
    """Resize a btrfs file system inside a partition."""
    try:
        command = ['btrfs', 'filesystem', 'resize', 'max', mount_point]
        subprocess.run(command, stdout=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as exception:
        raise RuntimeError(f'Error expanding filesystem: {exception}')


def _get_free_space(device):
    """Return the amount of free space after a partition."""
    device, partition_number = \
        _get_root_device_and_partition_number(device)

    try:
        requested_partition, free_spaces = \
            _get_partitions_and_free_spaces(device, partition_number)
    except Exception as exception:
        raise RuntimeError(f'Error getting partition details: {exception}')

    # Don't accept extended partitions for now
    if requested_partition['table_type'] == 'msdos' and \
       int(requested_partition['number']) >= 5:
        raise RuntimeError(
            'Expanding logical partitions currently unsupported')

    # Don't accept anything but btrfs and ext4 filesystems
    if requested_partition['type'] not in ('btrfs', 'ext4'):
        raise RuntimeError(
            f'Unsupported file system type: {requested_partition["type"]}')

    found_free_space = None
    for free_space in free_spaces:
        if free_space['start'] != requested_partition['end'] + 1:
            continue

        if free_space['size'] < 10 * 1024 * 1024:  # Minimum 10MiB
            continue

        found_free_space = free_space

    if not found_free_space:
        raise RuntimeError('No free space available')

    return device, requested_partition, found_free_space


def _get_partition_device(device, partition_number):
    """Return the device corresponding to a parition in a given device."""
    if re.match('[0-9]', device[-1]):
        return device + 'p' + str(partition_number)

    return device + str(partition_number)


def _get_root_device_and_partition_number(device):
    """Return the parent device and number of partition separately."""
    match = re.match(r'(.+[a-zA-Z]\d+)p(\d+)$', device)
    if not match:
        match = re.match(r'(.+[a-zA-Z])(\d+)$', device)
        if not match:
            raise ValueError('Invalid device, must be a partition')

    return match.group(1), match.group(2)


def _get_partitions_and_free_spaces(device, partition_number):
    """Run parted and return list of partitions and free spaces."""
    command = [
        'parted', '--machine', '--script', device, 'unit', 'B', 'print', 'free'
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, check=True)

    requested_partition = None
    free_spaces = []

    lines = process.stdout.decode().splitlines()
    partition_table_type = lines[1].split(':')[5]
    for line in lines[2:]:
        line = line.rstrip(';')
        keys = ('number', 'start', 'end', 'size', 'type')
        parts = line.split(':')
        segment = dict(zip(keys, parts[:5]))

        segment['table_type'] = partition_table_type
        segment['start'] = _interpret_unit(segment['start'])
        segment['end'] = _interpret_unit(segment['end'])
        segment['size'] = _interpret_unit(segment['size'])

        if segment['type'] == 'free':
            segment['number'] = None
            free_spaces.append(segment)
        else:
            if segment['number'] == partition_number:
                requested_partition = segment

    return requested_partition, free_spaces


def _interpret_unit(value):
    """Return value in bytes after understanding parted unit."""
    value = value.rstrip('B')  # For now, we only need to understand bytes
    return int(value)


@privileged
def mount(block_device: str):
    """Mount a disk are root user.

    XXX: This is primarily to provide compatibility with older code that used
    udiskie to auto-mount all partitions as root user under /media/root/
    directory. We are setting special permissions for the directory /media/root
    and users have set shared folders using this path. This can be removed in
    favor of using DBus API once we have a migration plan in place. Disks can
    be mounted directly /mount without ACL restrictions that apply to
    /mount/<user> directories. This can be done by setting udev flag
    UDISKS_FILESYSTEM_SHARED=1 by writing a udev rule.

    """
    subprocess.run([
        'udisksctl', 'mount', '--block-device', block_device,
        '--no-user-interaction'
    ], check=True)


@privileged
def eject(device_path: str) -> str:
    """Eject a device by its path."""
    return _eject_drive_of_device(device_path)


def _get_options():
    """Return the common options used for udisks2 operations."""
    glib = utils.import_from_gi('GLib', '2.0')
    options = glib.Variant(
        'a{sv}', {'auth.no_user_interaction': glib.Variant('b', True)})
    return options


def _eject_drive_of_device(device_path):
    """Eject a device after unmounting all of its partitions.

    Return the details (model, vendor) of drives ejected.
    """
    udisks = utils.import_from_gi('UDisks', '2.0')
    glib = utils.import_from_gi('GLib', '2.0')
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    found_objects = [
        obj for obj in object_manager.get_objects()
        if obj.get_block() and obj.get_block().props.device == device_path
    ]

    if not found_objects:
        raise ValueError(
            'No such device - {device_path}'.format(device_path=device_path))

    obj = found_objects[0]

    # Unmount filesystems
    block_device = obj.get_block()
    drive_object_path = block_device.props.drive
    if drive_object_path != '/':
        _umount_all_filesystems_of_drive(drive_object_path)
    else:
        # Block device has not associated drive
        _umount_filesystem(obj.get_filesystem())

    # Eject the drive
    drive = client.get_drive_for_block(block_device)
    if drive:
        try:
            drive.call_eject_sync(_get_options(), None)
        except glib.Error:
            # Ignore error during ejection as along as all the filesystems are
            # unmounted, the disk can be removed.
            pass

        return {
            'vendor': drive.props.vendor,
            'model': drive.props.model,
        }

    return None


def _umount_filesystem(filesystem):
    """Unmount a filesystem."""
    if filesystem and filesystem.props.mount_points:
        filesystem.call_unmount_sync(_get_options())


def _umount_all_filesystems_of_drive(drive_object_path):
    """Unmount all filesystems on block devices of a drive."""
    udisks = utils.import_from_gi('UDisks', '2.0')
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    for obj in object_manager.get_objects():
        block_device = obj.get_block()
        if not block_device or block_device.props.drive != drive_object_path:
            continue

        _umount_filesystem(obj.get_filesystem())


@privileged
def setup():
    """Configure storage."""
    # create udisks2 default mount directory
    mounts_directory = '/media/root'
    try:
        os.mkdir(mounts_directory)
    except FileExistsError:
        pass

    # make the directory readable and traversible by other users
    stats = os.stat(mounts_directory)
    os.chmod(mounts_directory, stats.st_mode | stat.S_IROTH | stat.S_IXOTH)


@privileged
def usage_info() -> str:
    """Get information about disk space usage."""
    command = [
        'df', '--exclude-type=tmpfs', '--exclude-type=devtmpfs',
        '--block-size=1', '--output=source,fstype,size,used,avail,pcent,target'
    ]
    return subprocess.check_output(command).decode()


@privileged
def validate_directory(directory: str, check_creatable: bool,
                       check_writable: bool):
    """Validate a directory."""
    if os.geteuid() == 0:
        raise RuntimeError('You must not be root to run this command')

    def part_exists(path):
        """Return part of the path that exists."""
        if not path or os.path.exists(path):
            return path
        return part_exists(os.path.dirname(path))

    if check_creatable:
        directory = part_exists(directory)
        if not directory:
            directory = '.'
    else:
        if not os.path.exists(directory):
            raise FileNotFoundError

    if not os.path.isdir(directory):
        raise NotADirectoryError

    if not os.access(directory, os.R_OK):
        raise PermissionError('read')

    if check_writable or check_creatable:
        if not os.access(directory, os.W_OK):
            raise PermissionError('write')
