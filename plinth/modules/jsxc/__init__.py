# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure XMPP web client/jsxc.
"""

import logging

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.web_server import StaticFiles

from . import manifest

_description = [
    _('JSXC is a web client for XMPP. Typically it is used with an XMPP '
      'server running locally.'),
]

logger = logging.getLogger(__name__)

app = None


class JSXCApp(app_module.App):
    """FreedomBox app for JSXC."""

    app_id = 'jsxc'

    _version = 1

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('JSXC'), icon_filename='jsxc',
                               short_description=_('Chat Client'),
                               description=_description, manual_page='JSXC',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-jsxc', info.name, info.short_description,
                              info.icon_filename, 'jsxc:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-jsxc', name=info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url=reverse_lazy('jsxc:jsxc'),
                                      clients=info.clients)
        self.add(shortcut)

        packages = Packages('packages-jsxc', ['libjs-jsxc'])
        self.add(packages)

        firewall = Firewall('firewall-jsxc', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        directory_map = {
            '/static/jsxc/img': '/usr/share/libjs-jsxc/img/',
            '/static/jsxc/libjs-jsxc/lib': '/usr/share/javascript/jsxc/lib/',
            '/static/jsxc/libjs-jsxc/sound': '/usr/share/libjs-jsxc/sound/',
            '/static/jsxc/libjs-jsxc/': '/usr/share/libjs-jsxc/css/',
        }
        static_files = StaticFiles('static-files-jsxc',
                                   directory_map=directory_map)
        self.add(static_files)

        backup_restore = BackupRestore('backup-restore-jsxc',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)
    helper.call('post', app.enable)
