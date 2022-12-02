# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure I2P."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.i2p.resources import FAVORITES
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('The Invisible Internet Project is an anonymous network layer intended '
      'to protect communication from censorship and surveillance. I2P '
      'provides anonymity by sending encrypted traffic through a '
      'volunteer-run network distributed around the world.'),
    _('Find more information about I2P on their project '
      '<a href="https://geti2p.net" target="_blank">homepage</a>.'),
    _('The first visit to the provided web interface will initiate the '
      'configuration process.')
]

tunnels_to_manage = {
    'I2P HTTP Proxy': 'i2p-http-proxy-freedombox',
    'I2P HTTPS Proxy': 'i2p-https-proxy-freedombox',
    'Irc2P': 'i2p-irc-freedombox'
}


class I2PApp(app_module.App):
    """FreedomBox app for I2P."""

    app_id = 'i2p'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'i2p': _('Manage I2P application')}

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('I2P'), icon_filename='i2p',
                               short_description=_('Anonymity Network'),
                               description=_description, manual_page='I2P',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-i2p', info.name, info.short_description,
                              info.icon_filename, 'i2p:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-i2p', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/i2p/',
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-i2p', ['i2p'])
        self.add(packages)

        firewall = Firewall('firewall-i2p-web', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall = Firewall('firewall-i2p-proxies', _('I2P Proxy'),
                            ports=tunnels_to_manage.values(),
                            is_external=False)
        self.add(firewall)

        webserver = Webserver('webserver-i2p', 'i2p-freedombox',
                              urls=['https://{host}/i2p/'])
        self.add(webserver)

        daemon = Daemon('daemon-i2p', 'i2p', listen_ports=[(7657, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-i2p',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-i2p', **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        self.disable()
        # Add favorites to the configuration
        for fav in FAVORITES:
            privileged.add_favorite(fav['name'], fav['url'],
                                    fav.get('description'), fav.get('icon'))

        # Tunnels to all interfaces
        for tunnel in tunnels_to_manage:
            privileged.set_tunnel_property(tunnel, 'interface', '0.0.0.0')

        self.enable()
