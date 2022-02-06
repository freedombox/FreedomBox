# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Zoph web application
"""

import json
import logging

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest

logger = logging.getLogger(__name__)

_description = [
    format_lazy(
        _('Zoph manages your photo collection. Photos are stored on your '
          '{box_name}, under your control. Instead of focusing on galleries '
          'for public display, Zoph focuses on managing them for your own '
          'use, organizing them by who took them, where they were taken, '
          'and who is in them. Photos can be linked to multiple hierarchical '
          'albums and categories. It is easy to find all photos containing a '
          'person, or photos taken on a date, or photos taken at a location '
          'using search, map and calendar views. Individual photos can be '
          'shared with others by sending a direct link.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('The {box_name} user who setup Zoph will also become the '
          'administrator in Zoph. For additional users, accounts must be '
          'created both in {box_name} and in Zoph with the same user name.'),
        box_name=_(cfg.box_name))
]

app = None


class ZophApp(app_module.App):
    """FreedomBox app for Zoph."""

    app_id = 'zoph'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Zoph'), icon_filename='zoph',
                               short_description=_('Photo Organizer'),
                               description=_description, manual_page='Zoph',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-zoph', info.name, info.short_description,
                              info.icon_filename, 'zoph:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-zoph', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/zoph/',
                                      clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-zoph', ['zoph'])
        self.add(packages)

        firewall = Firewall('firewall-zoph', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-zoph', 'zoph',
                              urls=['https://{host}/zoph/'])
        self.add(webserver)

        backup_restore = ZophBackupRestore('backup-restore-zoph',
                                           **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'zoph', ['pre-install'])
    app.setup(old_version)
    helper.call('post', actions.superuser_run, 'zoph', ['setup'])
    helper.call('post', app.enable)


def set_configuration(admin_user=None, enable_osm=None):
    """Configure Zoph."""
    args = []
    if admin_user:
        args += ['--admin-user', admin_user]

    if enable_osm is not None:
        args += ['--enable-osm', str(enable_osm)]

    actions.superuser_run('zoph', ['set-configuration'] + args)


def is_configured():
    """Return whether the Zoph app is configured."""
    output = actions.superuser_run('zoph', ['is-configured'])
    return output.strip() == 'true'


def get_configuration():
    """Return full configuration of Zoph."""
    configuration = actions.superuser_run('zoph', ['get-configuration'])
    return json.loads(configuration)


class ZophBackupRestore(BackupRestore):
    """Component to backup/restore Zoph database"""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        actions.superuser_run('zoph', ['dump-database'])

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        actions.superuser_run('zoph', ['restore-database'])
