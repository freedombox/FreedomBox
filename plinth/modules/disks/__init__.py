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
    """Returns list of disks by combining information from df and lsblk."""
    infos_df = _get_diskinfo_df()
    infos_lsblk = _get_diskinfo_lsblk()
    # Combine both sources of info dicts into one dict, based on mount point;
    # note this discards disks without a (current) mount point.
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
    for ddict in dev_dicts:
        ddict['dev_kname'] = '/dev/{0}'.format(ddict['kname'])
    return dev_dicts


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
