# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for janus.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.coturn.components import TurnTimeLimitedConsumer
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages, install
from plinth.utils import Version, format_lazy

from . import manifest, privileged

_description = [
    _('Janus is a lightweight WebRTC server.'),
    _('A simple video conference room is included.'),
    format_lazy(
        _('<a href="{coturn_url}">Coturn</a> is required to '
          'use Janus.'), coturn_url=reverse_lazy('coturn:index')),
]


class JanusApp(app_module.App):
    """FreedomBox app for janus."""

    app_id = 'janus'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(self.app_id, self._version, name=_('Janus'),
                               icon_filename='janus',
                               short_description=_('Video Room'),
                               description=_description, manual_page='Janus',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-janus', info.name, info.short_description,
                              info.icon_filename, 'janus:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-janus', info.name,
                                      info.short_description,
                                      info.icon_filename,
                                      reverse_lazy('janus:room'),
                                      clients=manifest.clients)
        self.add(shortcut)

        packages = Packages('packages-janus', [
            'janus', 'libjs-bootbox', 'libjs-bootstrap', 'libjs-bootswatch',
            'libjs-janus-gateway', 'libjs-jquery-blockui', 'libjs-spin.js',
            'libjs-toastr', 'libjs-webrtc-adapter'
        ])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-janus', [
            '/etc/apache2/conf-available/janus-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-janus', info.name,
                            ports=['http', 'https',
                                   'janus-freedombox'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-janus', 'janus-freedombox')
        self.add(webserver)

        daemon = Daemon(
            'daemon-janus', 'janus', listen_ports=[(8088, 'tcp4'),
                                                   (8088, 'tcp6'),
                                                   (8188, 'tcp4'),
                                                   (8188, 'tcp6')])
        self.add(daemon)

        turn = TurnTimeLimitedConsumer('turn-janus')
        self.add(turn)

        backup_restore = BackupRestore('backup-restore-janus',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

    def force_upgrade(self, packages):
        """Force upgrade janus to resolve conffile prompts."""
        if 'janus' not in packages:
            return False

        # Allow upgrades within 1.0.* and 1.1.*
        package = packages['janus']
        if Version(package['new_version']) > Version('1.2~'):
            return False

        install(['janus'], force_configuration='new')
        privileged.setup()
        return True
