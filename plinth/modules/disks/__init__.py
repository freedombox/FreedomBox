#
# This file is part of Plinth.
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
Plinth module to manage disks.
"""

from django.utils.translation import ugettext_lazy as _
import json
import logging
import subprocess

from plinth import actions
from plinth import cfg


version = 1

depends = ['system']

title = _('Disks')

description = []

service = None

logger = logging.getLogger(__name__)


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(title, 'glyphicon-hdd', 'disks:index')


def get_disks():
    """ FIXME """
    infos_df = _get_diskinfo_df()
    infos_lsblk = _get_diskinfo_lsblk()
    # Combine both sources of info-dicts into one dict, based on mount point;
    # note that this also discards disks without a (current) mount point,
    # which includes the parent devices returned by lsblk.
    combined_list = []
    for info_df in infos_df:
        for info_lsblk in infos_lsblk:
            if info_df['mount_point'] == info_lsblk['mountpoint']:
                info_df.update(info_lsblk)
                combined_list.append(info_df)
    return combined_list


def _get_diskinfo_df():
    """Return the list of disks and free space available."""
    command = ['df', '--exclude-type=tmpfs', '--exclude-type=devtmpfs',
               '--output=source,target,fstype,size,used,pcent',
               '--human-readable']
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []

    output = process.stdout.decode()

    disks = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        keys = ('device', 'mount_point', 'file_system_type', 'size', 'used',
                'percentage_used')
        disk = dict(zip(keys, parts))
        disk['percentage_used'] = int(disk['percentage_used'].rstrip('%'))
        disks.append(disk)

    return disks


def _get_diskinfo_lsblk():
    """Return the list of disks and free space available."""
    command = ['lsblk', '--json', '--output', 'kname,pkname,mountpoint,type']
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []

    output = process.stdout.decode()
    dev_dicts = json.loads(output)['blockdevices']
    return dev_dicts


def get_root_device(disks):
    """Return the root partition's device from list of partitions."""
    devices = [disk['device'] for disk in disks if disk['mount_point'] == '/']
    try:
        return devices[0]
    except IndexError:
        return None


def get_root_device2(disks):
    """Return the root partition's device from list of partitions."""
    devices = ['/dev/{0}'.format(disk['kname']) for disk in disks
               if disk['mountpoint'] == '/']
    try:
        return devices[0]
    except IndexError:
        return None


def is_expandable(device):
    """Return the list of partitions that can be expanded."""
    if not device:
        return False

    try:
        output = actions.superuser_run(
            'disks', ['is-partition-expandable', device])
    except actions.ActionError:
        return False

    return int(output.strip())


def expand_partition(device):
    """Expand a partition."""
    actions.superuser_run('disks', ['expand-partition', device])


if __name__ == '__main__':
    disksOld = _get_diskinfo_df()
    print("Output of (old) _get_diskinfo_df():")
    print(disksOld)
    print("\nOLD output of get_root_device():")
    print(get_root_device(disksOld))
    print("\n----------------------------------")
    disksNew = _get_diskinfo_lsblk()
    print("\nOutput of (new) _get_diskinfo_lsblk():")
    print(disksNew)
    print("\nNEW output of get_root_device2():")
    print(get_root_device2(disksNew))
    print('\n----------------------------------')
    print('New, combined output of get_disks():')
    print(get_disks())
