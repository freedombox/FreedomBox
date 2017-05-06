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
import logging
import subprocess
import json

from plinth import actions
from plinth.menu import main_menu


version = 1

title = _('Disks')

description = []

service = None

logger = logging.getLogger(__name__)


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-hdd', 'disks:index')


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


def _get_disks_from_df():
    """Return the list of disks and free space available using 'df'."""
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
    devices = [disk['dev_kname'] for disk in disks
               if disk['mountpoint'] == '/' and disk['type'] == 'part']
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
