# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to manage filesystem snapshots.
"""

import json
import pathlib

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu
from plinth.modules import storage
from plinth.modules.backups.components import BackupRestore

from . import manifest

version = 4

is_essential = True

managed_packages = ['snapper']

_description = [
    _('Snapshots allows creating and managing btrfs file system snapshots. '
      'These can be used to roll back the system to a previously known '
      'good state in case of unwanted changes to the system.'),
    # Translators: xgettext:no-python-format
    _('Snapshots are taken periodically (called timeline snapshots) and also '
      'before and after a software installation. Older snapshots will be '
      'automatically cleaned up according to the settings below.'),
    _('Snapshots currently work on btrfs file systems only and on the root '
      'partition only. Snapshots are not a replacement for '
      '<a href="/plinth/sys/backups">backups</a> since '
      'they can only be stored on the same partition. ')
]

DEFAULT_FILE = '/etc/default/snapper'

fs_types_supported = ['btrfs']

app = None


class SnapshotApp(app_module.App):
    """FreedomBox app for snapshots."""

    app_id = 'snapshot'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Storage Snapshots'), icon='fa-film',
                               description=_description,
                               manual_page='Snapshots')
        self.add(info)

        menu_item = menu.Menu('menu-snapshot', info.name, None, info.icon,
                              'snapshot:index', parent_url_name='system')
        self.add(menu_item)

        backup_restore = SnapshotBackupRestore('backup-restore-snapshot',
                                               **manifest.backup)
        self.add(backup_restore)


class SnapshotBackupRestore(BackupRestore):
    """Component to backup/restore snapshot module."""

    def restore_post(self, packet):
        """Run after restore."""
        actions.superuser_run('snapshot', ['kill-daemon'])


def is_supported():
    """Return whether snapshots are support on current setup."""
    fs_type = storage.get_filesystem_type()
    # Check that / is not a bind mounted btrfs filesystem similar to how
    # snapper does the check: https://github.com/openSUSE/snapper/blob/
    # 77eb6565d3d8df95a06cd52ce31174d98994939c/snapper/BtrfsUtils.cc#L61
    root_inode_number = pathlib.Path('/').stat().st_ino
    return fs_type in fs_types_supported and root_inode_number == 256


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    if is_supported():
        helper.call('post', actions.superuser_run, 'snapshot',
                    ['setup', '--old-version',
                     str(old_version)])
        helper.call('post', app.enable)


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

    # shell-script config file lens
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DEFAULT_FILE)
    aug.load()
    return aug


def is_apt_snapshots_enabled(aug):
    """Return whether APT snapshots is enabled."""
    value = aug.get('/files' + DEFAULT_FILE + '/DISABLE_APT_SNAPSHOT')
    return value != 'yes'


def get_configuration():
    aug = load_augeas()
    output = actions.superuser_run('snapshot', ['get-config'])
    output = json.loads(output)

    def get_boolean_choice(status):
        return ('yes', 'Enabled') if status else ('no', 'Disabled')

    def get_max_from_range(key):
        return output[key].split('-')[-1]

    return {
        'enable_timeline_snapshots':
            get_boolean_choice(output['TIMELINE_CREATE'] == 'yes'),
        'enable_software_snapshots':
            get_boolean_choice(is_apt_snapshots_enabled(aug)),
        'hourly_limit':
            get_max_from_range('TIMELINE_LIMIT_HOURLY'),
        'daily_limit':
            get_max_from_range('TIMELINE_LIMIT_DAILY'),
        'weekly_limit':
            get_max_from_range('TIMELINE_LIMIT_WEEKLY'),
        'monthly_limit':
            get_max_from_range('TIMELINE_LIMIT_MONTHLY'),
        'yearly_limit':
            get_max_from_range('TIMELINE_LIMIT_YEARLY'),
        'free_space':
            output['FREE_LIMIT'],
    }
