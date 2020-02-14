#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to manage storage.
"""

import logging
import subprocess

import psutil
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from plinth import actions
from plinth import app as app_module
from plinth import cfg, glib, menu, utils
from plinth.daemon import Daemon
from plinth.errors import ActionError, PlinthError
from plinth.utils import format_lazy, import_from_gi

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 4

name = _('Storage')

managed_services = ['freedombox-udiskie']

managed_packages = ['parted', 'udiskie', 'gir1.2-udisks-2.0']

description = [
    format_lazy(
        _('This module allows you to manage storage media attached to your '
          '{box_name}. You can view the storage media currently in use, mount '
          'and unmount removable media, expand the root partition etc.'),
        box_name=_(cfg.box_name))
]

logger = logging.getLogger(__name__)

manual_page = 'Storage'

is_essential = True

app = None


class StorageApp(app_module.App):
    """FreedomBox app for storage."""

    app_id = 'storage'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-storage', name, None, 'fa-hdd-o',
                              'storage:index', parent_url_name='system')
        self.add(menu_item)

        daemon = Daemon('daemon-udiskie', managed_services[0])
        self.add(daemon)

        # Check every hour for low disk space, every 3 minutes in debug mode
        interval = 180 if cfg.develop else 3600
        glib.schedule(interval, warn_about_low_disk_space)


def init():
    """Initialize the module."""
    global app
    app = StorageApp()
    app.set_enabled(True)


def get_disks():
    """Returns list of disks by combining information from df and udisks."""
    disks = _get_disks_from_df()
    disks_from_udisks = _get_disks_from_udisks()

    # Add info from udisks to the disks from df based on mount point.
    for disk_from_df in disks:
        for disk_from_udisks in disks_from_udisks:
            if disk_from_udisks['mount_point'] == disk_from_df['mount_point']:
                disk_from_df.update(disk_from_udisks)

    return sorted(disks, key=lambda disk: disk['device'])


def _get_disks_from_udisks():
    """List devices that can be ejected."""
    udisks = utils.import_from_gi('UDisks', '2.0')
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()
    devices = []

    for obj in object_manager.get_objects():

        if not obj.get_block():
            continue

        block = obj.get_block()

        if block.props.id_usage != 'filesystem':
            continue

        device = {
            'device': block.props.device,
            'label': block.props.id_label,
            'size': format_bytes(block.props.size),
            'filesystem_type': block.props.id_type,
            'is_removable': not block.props.hint_system
        }
        try:
            device['mount_point'] = obj.get_filesystem().props.mount_points[0]
        except Exception:
            continue
        devices.append(device)

    return devices


def _get_disks_from_df():
    """Return the list of disks and free space available using 'df'."""
    try:
        output = actions.superuser_run('storage', ['usage-info'])
    except subprocess.CalledProcessError as exception:
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
    """Returns the type of the filesystem mounted at mountpoint."""
    for partition in psutil.disk_partitions():
        if partition.mountpoint == mount_point:
            return partition.fstype

    raise ValueError('No such mount point')


def get_disk_info(mount_point):
    """Get information about the free space of a drive"""
    disks = get_disks()
    list_root = [disk for disk in disks if disk['mount_point'] == mount_point]
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
        if disk['mount_point'] == '/':
            return disk['device']
    return None


def is_expandable(device):
    """Return the list of partitions that can be expanded."""
    if not device:
        return False

    try:
        output = actions.superuser_run('storage',
                                       ['is-partition-expandable', device],
                                       log_error=False)
    except actions.ActionError:
        return False

    return int(output.strip())


def expand_partition(device):
    """Expand a partition."""
    actions.superuser_run('storage', ['expand-partition', device])


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
    udisks = import_from_gi('UDisks', '2.0')
    if error.matches(udisks.Error.quark(), udisks.Error.FAILED):
        message = _('The operation failed.')
    elif error.matches(udisks.Error.quark(), udisks.Error.CANCELLED):
        message = _('The operation was cancelled.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_UNMOUNTING):
        message = _('The device is already unmounting.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_SUPPORTED):
        message = _('The operation is not supported due to '
                    'missing driver/tool support.')
    elif error.matches(udisks.Error.quark(), udisks.Error.TIMED_OUT):
        message = _('The operation timed out.')
    elif error.matches(udisks.Error.quark(), udisks.Error.WOULD_WAKEUP):
        message = _('The operation would wake up a disk that is '
                    'in a deep-sleep state.')
    elif error.matches(udisks.Error.quark(), udisks.Error.DEVICE_BUSY):
        message = _('Attempting to unmount a device that is busy.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_CANCELLED):
        message = _('The operation has already been cancelled.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_AUTHORIZED) or \
        error.matches(udisks.Error.quark(),
                      udisks.Error.NOT_AUTHORIZED_CAN_OBTAIN) or \
        error.matches(udisks.Error.quark(),
                      udisks.Error.NOT_AUTHORIZED_DISMISSED):
        message = _('Not authorized to perform the requested operation.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_MOUNTED):
        message = _('The device is already mounted.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_MOUNTED):
        message = _('The device is not mounted.')
    elif error.matches(udisks.Error.quark(),
                       udisks.Error.OPTION_NOT_PERMITTED):
        message = _('Not permitted to use the requested option.')
    elif error.matches(udisks.Error.quark(),
                       udisks.Error.MOUNTED_BY_OTHER_USER):
        message = _('The device is mounted by another user.')
    else:
        message = error.message

    return message


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages, skip_recommends=True)
    helper.call('post', actions.superuser_run, 'storage', ['setup'])
    helper.call('post', app.enable)
    disks = get_disks()
    root_device = get_root_device(disks)
    if is_expandable(root_device):
        try:
            expand_partition(root_device)
        except ActionError:
            pass


def warn_about_low_disk_space(request):
    """Warn about insufficient space on root partition."""
    from plinth.notification import Notification

    try:
        root_info = get_disk_info('/')
    except PlinthError as exception:
        logger.exception('Error getting information about root partition: %s',
                         exception)
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
        message = ugettext_noop(
            # xgettext:no-python-format
            'Low space on system partition: {percent_used}% used, '
            '{free_space} free.')
        title = ugettext_noop('Low disk space')
        data = {
            'app_icon': 'fa-hdd-o',
            'app_name': ugettext_noop('Storage'),
            'percent_used': root_info['percent_used'],
            'free_space': format_bytes(root_info['free_bytes'])
        }
        actions = [{
            'type': 'link',
            'class': 'primary',
            'text': 'Go to {app_name}',
            'url': 'storage:index'
        }, {
            'type': 'dismiss'
        }]
        Notification.update_or_create(id='storage-low-disk-space',
                                      app_id='storage', severity=severity,
                                      title=title, message=message,
                                      actions=actions, data=data,
                                      group='admin')
