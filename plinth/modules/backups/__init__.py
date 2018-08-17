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
FreedomBox app to manage backup archives.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu
from plinth.modules import udiskie

version = 1

managed_packages = ['borgbackup']

name = _('Backups')

description = [_('Backups allows creating and managing backup archives.'), ]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-duplicate', 'backups:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups', ['setup'])


def get_info():
    output = actions.superuser_run('backups', ['info'])
    return json.loads(output)


def list_archives():
    output = actions.superuser_run('backups', ['list'])
    return json.loads(output)['archives']


def get_archive(name):
    for archive in list_archives():
        if archive['name'] == name:
            return archive

    return None


def create_archive(name, path):
    actions.superuser_run('backups',
                          ['create', '--name', name, '--path', path])


def delete_archive(name):
    actions.superuser_run('backups', ['delete', '--name', name])


def export_archive(name, location):
    if location[-1] != '/':
        location += '/'
    filename = location + 'FreedomBox-backups/' + name + '.tar.gz'
    actions.superuser_run('backups',
                          ['export', '--name', name, '--filename', filename])


def get_export_locations():
    """Return a list of storage locations for exported backup archives."""
    locations = [('/var/lib/freedombox/', _('Root Filesystem'))]
    if udiskie.is_running():
        devices = udiskie.udisks2.list_devices()
        for device in devices:
            if 'mount_points' in device and len(device['mount_points']) > 0:
                name = device['label'] or device['device']
                locations.append((device['mount_points'][0], name))

    return locations


def get_export_files():
    """Return a dict of exported backup archives found in storage locations."""
    locations = get_export_locations()
    export_files = {}
    for location in locations:
        output = actions.superuser_run(
            'backups', ['list-exports', '--location',  location[0]])
        export_files[location[1]] = json.loads(output)

    return export_files


def restore_exported(label, name):
    """Restore files from exported backup archive."""
    locations = get_export_locations()
    for location in locations:
        if location[1] == label:
            filename = location[0]
            if filename[-1] != '/':
                filename += '/'
            filename += 'FreedomBox-backups/' + name
            actions.superuser_run(
                'backups', ['restore', '--filename', filename])
            break
