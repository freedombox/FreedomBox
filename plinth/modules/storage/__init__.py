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
import json
import logging
import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, cfg
from plinth.errors import PlinthError
from plinth.menu import main_menu
from plinth.utils import format_lazy, is_user_admin

from .manifest import backup

version = 3

name = _('Storage')

managed_services = ['freedombox-udiskie']

managed_packages = ['udiskie', 'gir1.2-udisks-2.0']

description = [
    format_lazy(
        _('This module allows you to manage storage media attached to your '
          '{box_name}. You can view the storage media currently in use, mount '
          'and unmount removable media, expand the root partition etc.'),
        box_name=_(cfg.box_name))
]

service = None

logger = logging.getLogger(__name__)

manual_page = 'Storage'

is_essential = True


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-hdd', 'storage:index')


def get_disks():
    """Returns list of disks by combining information from df and lsblk."""
    disks_from_df = _get_disks_from_df()
    disks_from_lsblk = _get_disks_from_lsblk()
    # Combine both sources of info dicts into one dict, based on mount point;
    # note this discards disks without a (current) mount point.
    combined_list = []
    for disk_from_df in disks_from_df:
        for disk_from_lsblk in disks_from_lsblk:
            if disk_from_df['mount_point'] == disk_from_lsblk['mountpoint']:
                disk_from_df.update(disk_from_lsblk)
                combined_list.append(disk_from_df)

    return combined_list


def get_disk_info(mountpoint, request):
    """Get information about the free space of a drive"""
    if not is_user_admin(request, cached=True):
        raise PermissionError
    disks = get_disks()
    list_root = [disk for disk in disks if disk['mountpoint'] == mountpoint]
    if not list_root:
        raise PlinthError
    percent_used = list_root[0]['percent_used']
    free_bytes = list_root[0]['free']
    free_gib = free_bytes / (1024**3)
    return {
        "percent_used": percent_used,
        "free_bytes": free_bytes,
        "free_gib": free_gib
    }


def _get_disks_from_df():
    """Return the list of disks and free space available using 'df'."""
    command = [
        'df', '--exclude-type=tmpfs', '--exclude-type=devtmpfs',
        '--block-size=1', '--output=source,fstype,size,used,avail,pcent,target'
    ]
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []

    output = process.stdout.decode()

    disks = []
    for line in output.splitlines()[1:]:
        parts = line.split(maxsplit=6)
        keys = ('device', 'file_system_type', 'size', 'used', 'free',
                'percent_used', 'mount_point')
        disk = dict(zip(keys, parts))
        disk['percent_used'] = int(disk['percent_used'].rstrip('%'))
        disk['size'] = int(disk['size'])
        disk['used'] = int(disk['used'])
        disk['free'] = int(disk['free'])
        disk['size_str'] = format_bytes(disk['size'])
        disk['used_str'] = format_bytes(disk['used'])
        disk['free_str'] = format_bytes(disk['free'])
        disks.append(disk)

    return disks


def _get_disks_from_lsblk():
    """Return the list of disks and other information from 'lsblk'."""
    command = ['lsblk', '--json', '--output', 'kname,pkname,mountpoint,type']
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []

    output = process.stdout.decode()
    disks = json.loads(output)['blockdevices']
    for disk in disks:
        disk['dev_kname'] = '/dev/{0}'.format(disk['kname'])

    return disks


def get_root_device(disks):
    """Return the root partition's device from list of partitions."""
    devices = [
        disk['dev_kname'] for disk in disks
        if disk['mountpoint'] == '/' and disk['type'] == 'part'
    ]
    try:
        return devices[0]
    except IndexError:
        return None


def is_expandable(device):
    """Return the list of partitions that can be expanded."""
    if not device:
        return False

    try:
        output = actions.superuser_run('storage',
                                       ['is-partition-expandable', device])
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


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('freedombox-udiskie')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('freedombox-udiskie')


def enable():
    """Enable the module."""
    actions.superuser_run('udiskie', ['enable'])


def disable():
    """Disable the module."""
    actions.superuser_run('udiskie', ['disable'])


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages, skip_recommends=True)
    helper.call('post', actions.superuser_run, 'udiskie', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], name, ports=[], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    disks = get_disks()
    root_device = get_root_device(disks)
    if is_expandable(root_device):
        expand_partition(root_device)
