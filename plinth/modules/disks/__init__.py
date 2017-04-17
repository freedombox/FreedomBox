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

def get_disks_new():
    """Return the list of disks and free space available."""
    command = ['lsblk', '--json', '--bytes', '--output-all']
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exception:
        logger.exception('Error getting disk information: %s', exception)
        return []  # TODO: or raise an "Failed Action exception"?

    output = process.stdout.decode()
    out_dict = json.loads(output)
    dev_dicts = out_dict['blockdevices']
    # The output dict may contain nested sub-dicts at 'children'.
    # This hierarchy is flattened into a list (without sub-lists),
    # containing parent devices p1, p2, ..., and their children ...
    # TODO: more description
    
    # FIXME: Why/how does commenting in the next 2 lines impact the 3rd??
#    dev_list = []
#    dev_list.extend(_subdict_to_list(dev_dict) for dev_dict in dev_dicts)
    dev_list = _subdict_to_list(dev_dicts[0])  # FIXME: fix above line
    return dev_list

def _subdict_to_list(dev_json):
    # do depth-first walk into device dict hierarchy, append children to list
    if 'children' not in dev_json.keys():
        children = None
    else:
        children = dev_json.pop('children')
    if children is None:
        return dev_json
    else:  # recursively accumulate sub-dicts
        out_list = []
        out_list.append(dev_json)  # add parent, then follow children
        out_list.extend(_subdict_to_list(sub_dict) for sub_dict in children)
        return out_list

def get_root_device(disks):
    """Return the root partition's device from list of partitions."""
    devices = [disk['device'] for disk in disks if disk['mount_point'] == '/']
    try:
        return devices[0]
    except IndexError:
        return None

def get_root_device2(disks):
    """Return the root partition's device from list of partitions."""
    devices = [disk['name'] for disk in disks if disk['mountpoint'] == '/']
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
    disksOld = get_disks()
    print("OLD output of get_disks():")
    print(disksOld)
    print("\nOLD output of get_root_device():")
    print(get_root_device(disksOld))
    
    disksNew = get_disks_new()
    print("\nNEW output of get_disks_new():")
    print(disksNew)
    print("\nNEW output of get_root_device2():")
    print(get_root_device2(disksNew))
