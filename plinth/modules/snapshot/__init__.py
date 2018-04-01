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
FreedomBox app to manage filesystem snapshots.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu

version = 3

managed_packages = ['snapper']

name = _('Storage Snapshots')

description = [
    _('Snapshots allows creating and managing btrfs file system snapshots. '
      'These can be used to roll back the system to a previously known '
      'good state in case of unwanted changes to the system.'),
    # Translators: xgettext:no-python-format
    _('Snapshots are taken every hour, day and month (called timeline '
      'snapshots). Snapshots are also taken before and after a software '
      'installation. Although snapshots are efficient and only store the '
      'differences, they may be deleted to reclaim free space.  Individual '
      'files from older snapshots can be accessed by visiting "/.snapshots" '
      'directory in the filesystem. It is recommended to enable snapshots '
      'only if you have at least 50% free space on your root partition.'),
    _('Snapshots work on btrfs file systems only and on the root '
      'partition only. Snapshots are not a replacement for backups since '
      'they are stored on the same partition. ')
]

service = None

manual_page = 'Snapshots'


def init():
    """Initialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-film', 'snapshot:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'snapshot', ['setup'])


def get_configuration():
    output = actions.superuser_run('snapshot', ['get-config'])
    output = json.loads(output)

    def get_boolean_choice(status):
        return ('yes', 'Enabled') if status else ('no', 'Disabled')

    return {
        'enable_timeline_snapshots':
            get_boolean_choice(output['TIMELINE_CREATE'] == 'yes'),
        'hourly_limit':
            output['TIMELINE_LIMIT_HOURLY'],
        'daily_limit':
            output['TIMELINE_LIMIT_DAILY'],
        'weekly_limit':
            output['TIMELINE_LIMIT_WEEKLY'],
        'yearly_limit':
            output['TIMELINE_LIMIT_YEARLY'],
        'monthly_limit':
            output['TIMELINE_LIMIT_MONTHLY'],
        'number_min_age':
            round(int(output['NUMBER_MIN_AGE']) / 86400),
    }
