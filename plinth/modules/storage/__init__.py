# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to manage storage."""

import base64
import logging
import subprocess

import psutil
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import cfg, glib, menu
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.errors import PlinthError
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged, udisks2

_description = [
    format_lazy(
        _('This module allows you to manage storage media attached to your '
          '{box_name}. You can view the storage media currently in use, mount '
          'and unmount removable media, expand the root partition etc.'),
        box_name=_(cfg.box_name))
]

logger = logging.getLogger(__name__)


class StorageApp(app_module.App):
    """FreedomBox app for storage."""

    app_id = 'storage'

    _version = 4

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Storage'),
                               icon='fa-hdd-o', description=_description,
                               manual_page='Storage', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-storage', info.name, info.icon, info.tags,
                              'storage:index', parent_url_name='system:data',
                              order=30)
        self.add(menu_item)

        packages = Packages('packages-storage',
                            ['parted', 'udisks2', 'gir1.2-udisks-2.0'])
        self.add(packages)

        backup_restore = BackupRestore('backup-restore-storage',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        # Check every hour for low disk space
        glib.schedule(3600, warn_about_low_disk_space)

        # Schedule initialization of UDisks2 initialization
        glib.schedule(3, udisks2.init, repeat=False)

        # Check periodically for a read-only root filesystem
        glib.schedule(600, _warn_about_read_only_filesystem)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        self.enable()
        disks = get_disks()
        root_device = get_root_device(disks)
        if is_expandable(root_device):
            try:
                privileged.expand_partition(root_device)
            except Exception:
                pass

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()
        result = _diagnose_grub_configured()
        if result:
            results.append(result)

        return results


def get_disks():
    """Return list of disks and their free space.

    The primary source of information is UDisks' list of block devices.
    Information from df is used for free space available.

    """
    disks_from_df = _get_disks_from_df()
    disks = udisks2.get_disks()
    for disk in disks:
        disk['size'] = format_bytes(disk['size'])

    # Add info from df to the disks from udisks based on mount point.
    for disk in disks:
        for disk_from_df in disks_from_df:
            if disk_from_df['mount_point'] in disk['mount_points']:
                disk['mount_point'] = disk_from_df['mount_point']
                for key in ('percent_used', 'size', 'used', 'free', 'size_str',
                            'used_str', 'free_str'):
                    disk[key] = disk_from_df[key]

    return sorted(disks, key=lambda disk: disk['device'])


def get_mounts():
    """Return list of mounts by combining information from df and UDisks.

    The primary source of information is the df command. Information from
    UDisks is used for labels.

    """
    disks = _get_disks_from_df()
    disks_from_udisks = udisks2.get_disks()
    for disk in disks_from_udisks:
        disk['size'] = format_bytes(disk['size'])

    # Add info from udisks to the disks from df based on mount point.
    for disk_from_df in disks:
        for disk_from_udisks in disks_from_udisks:
            if disk_from_df['mount_point'] in disk_from_udisks['mount_points']:
                disk_from_df.update(disk_from_udisks)

    return sorted(disks, key=lambda disk: disk['device'])


def _get_disks_from_df():
    """Return the list of disks and free space available using 'df'."""
    try:
        output = privileged.usage_info()
    except Exception as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []

    disks = []
    for line in output.splitlines()[1:]:
        parts = line.split(maxsplit=6)
        keys = ('device', 'filesystem_type', 'size', 'used', 'free',
                'percent_used', 'mount_point')
        disk = dict(zip(keys, parts))
        disk['percent_used'] = int(disk['percent_used'].rstrip('%'))
        disk['size'] = int(disk['size'])
        disk['used'] = int(disk['used'])
        disk['free'] = int(disk['free'])
        disk['size_str'] = format_bytes(disk['size'])
        disk['used_str'] = format_bytes(disk['used'])
        disk['free_str'] = format_bytes(disk['free'])
        disk['label'] = None
        disk['is_removable'] = None
        disks.append(disk)

    return disks


def get_filesystem_type(mount_point='/'):
    """Return the type of the filesystem mounted at mountpoint."""
    for partition in psutil.disk_partitions(all=True):
        if partition.mountpoint == mount_point:
            return partition.fstype

    raise ValueError('No such mount point')


def get_mount_info(mount_point):
    """Get information about the free space of a mount point."""
    mounts = get_mounts()
    list_root = [
        mount for mount in mounts if mount_point == mount['mount_point']
    ]
    if not list_root:
        raise PlinthError('Mount point {} not found.'.format(mount_point))

    percent_used = list_root[0]['percent_used']
    free_bytes = list_root[0]['free']
    free_gib = free_bytes / (1024**3)
    return {
        'percent_used': percent_used,
        'free_bytes': free_bytes,
        'free_gib': free_gib
    }


def get_root_device(disks):
    """Return the root partition's device from list of partitions."""
    for disk in disks:
        if '/' in disk['mount_points']:
            return disk['device']

    return None


def is_expandable(device):
    """Return the list of partitions that can be expanded."""
    if not device:
        return False

    try:
        return privileged.is_partition_expandable(device, _log_error=False)
    except Exception:
        return False


def format_bytes(size):
    """Return human readable disk size from bytes."""
    if not size:
        return size

    if size < 1024:
        return _('{disk_size:.1f} bytes').format(disk_size=size)

    if size < 1024**2:
        size /= 1024
        return _('{disk_size:.1f} KiB').format(disk_size=size)

    if size < 1024**3:
        size /= 1024**2
        return _('{disk_size:.1f} MiB').format(disk_size=size)

    if size < 1024**4:
        size /= 1024**3
        return _('{disk_size:.1f} GiB').format(disk_size=size)

    size /= 1024**4
    return _('{disk_size:.1f} TiB').format(disk_size=size)


def get_error_message(error):
    """Return an error message given an exception."""
    error_parts = error.split(':')
    if error_parts[0] != 'udisks-error-quark':
        return error

    short_error = error_parts[2].strip().split('.')[-1]
    message_map = {
        'Failed':
            _('The operation failed.'),
        'Cancelled':
            _('The operation was cancelled.'),
        'AlreadyUnmounting':
            _('The device is already unmounting.'),
        'NotSupported':
            _('The operation is not supported due to missing driver/tool '
              'support.'),
        'TimedOut':
            _('The operation timed out.'),
        'WouldWakeup':
            _('The operation would wake up a disk that is in a deep-sleep '
              'state.'),
        'DeviceBusy':
            _('Attempting to unmount a device that is busy.'),
        'AlreadyCancelled':
            _('The operation has already been cancelled.'),
        'NotAuthorized':
            _('Not authorized to perform the requested operation.'),
        'NotAuthorizedCanObtain':
            _('Not authorized to perform the requested operation.'),
        'NotAuthorizedDismissed':
            _('Not authorized to perform the requested operation.'),
        'AlreadyMounted':
            _('The device is already mounted.'),
        'NotMounted':
            _('The device is not mounted.'),
        'OptionNotPermitted':
            _('Not permitted to use the requested option.'),
        'MountedByOtherUser':
            _('The device is mounted by another user.')
    }
    return message_map.get(short_error, error)


def warn_about_low_disk_space(_data):
    """Warn about insufficient space on root partition."""
    from plinth.notification import Notification

    try:
        root_info = get_mount_info('/')
    except PlinthError:
        return

    show = False
    if root_info['percent_used'] > 90 or root_info['free_gib'] < 1:
        severity = 'error'
        show = True
    elif root_info['percent_used'] > 75 or root_info['free_gib'] < 2:
        severity = 'warning'
        show = True

    if not show:
        try:
            Notification.get('storage-low-disk-space').delete()
        except KeyError:
            pass
    else:
        message = gettext_noop(
            # xgettext:no-python-format
            'Low space on system partition: {percent_used}% used, '
            '{free_space} free.')
        title = gettext_noop('Low disk space')
        data = {
            'app_icon': 'fa-hdd-o',
            'app_name': 'translate:' + gettext_noop('Storage'),
            'percent_used': root_info['percent_used'],
            'free_space': format_bytes(root_info['free_bytes'])
        }
        actions = [{
            'type': 'link',
            'class': 'primary',
            'text': gettext_noop('Go to {app_name}'),
            'url': 'storage:index'
        }, {
            'type': 'dismiss'
        }]
        Notification.update_or_create(id='storage-low-disk-space',
                                      app_id='storage', severity=severity,
                                      title=title, message=message,
                                      actions=actions, data=data,
                                      group='admin')


def report_failing_drive(id, is_failing):
    """Show or withdraw notification about failing drive."""
    notification_id = 'storage-disk-failure-' + base64.b32encode(
        id.encode()).decode()

    from plinth.notification import Notification
    title = gettext_noop('Disk failure imminent')
    message = gettext_noop(
        'Disk {id} is reporting that it is likely to fail in the near future. '
        'Copy any data while you still can and replace the drive.')
    data = {
        'app_icon': 'fa-hdd-o',
        'app_name': 'translate:' + gettext_noop('Storage'),
        'id': id
    }
    note = Notification.update_or_create(id=notification_id, app_id='storage',
                                         severity='error', title=title,
                                         message=message, actions=[{
                                             'type': 'dismiss'
                                         }], data=data, group='admin')
    note.dismiss(should_dismiss=not is_failing)


def is_partition_read_only(mount_point='/'):
    """Return True if the partition is mounted read-only."""
    for partition in psutil.disk_partitions(all=True):
        if partition.mountpoint == mount_point:
            return 'ro' in partition.opts.split(',')

    raise ValueError('No such mount point')


def _warn_about_read_only_filesystem(_data):
    """Create a notification if the root filesystem is mounted read-only.

    Remove the notification (if any) if the root filesystem is writable.
    """
    from plinth.notification import Notification

    show = is_partition_read_only()
    notification_id = 'storage-read-only-root-filesystem'

    if not show:
        try:
            Notification.get(notification_id).delete()
        except KeyError:
            pass

        return

    message = gettext_noop(
        # xgettext:no-python-format
        'You cannot save configuration changes. Try rebooting the system. If '
        'the problem persists after a reboot, check the storage device for '
        'errors.')
    title = gettext_noop('Read-only root filesystem')
    data = {
        'app_icon': 'fa-hdd-o',
        'app_name': 'translate:' + gettext_noop('Storage'),
    }

    # This is a serious issue so the notification can't be dismissed.
    actions = [{
        'type': 'link',
        'class': 'primary',
        'text': gettext_noop('Go to Power'),
        'url': 'power:index'
    }]

    Notification.update_or_create(id=notification_id, app_id='storage',
                                  severity='error', title=title,
                                  message=message, actions=actions, data=data,
                                  group='admin')


def _diagnose_grub_configured() -> DiagnosticCheck | None:
    """Check if grub-pc package configuration failed.

    This detects an error that will occur during upgrades if GRUB
    install device is not selected.
    """
    result = None
    try:
        status = subprocess.check_output([
            'dpkg-query', '--show', '--showformat=${db:Status-Abbrev}',
            'grub-pc'
        ]).decode().strip()
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            return None

        raise err

    if status[0] != 'i':
        logger.info('grub-pc is not installed')
        return None

    # grub-pc should be installed
    if status[1] == 'i':  # installed
        logger.info('grub-pc is installed and configured')
        result = Result.PASSED
    elif status[1] == 'F':  # failed configuration
        logger.info('grub-pc is installed but failed configuration')
        result = Result.FAILED
    else:  # some other status
        logger.info('grub-pc is installed with status: %s', status[1])
        result = Result.WARNING

    return DiagnosticCheck('storage-grub-configured',
                           gettext_noop('grub package is configured'), result)
