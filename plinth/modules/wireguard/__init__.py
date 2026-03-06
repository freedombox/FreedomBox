# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for wireguard.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy, import_from_gi

from . import manifest, utils

nm = import_from_gi('NM', '1.0')

_description = [
    _('WireGuard is a fast, modern, secure VPN tunnel.'),
    format_lazy(
        _('It can be used to connect to a VPN provider which supports '
          'WireGuard, and to route all outgoing traffic from {box_name} '
          'through the VPN.'), box_name=_(cfg.box_name)),
    format_lazy(
        _('A second use case is to connect a mobile device to {box_name} '
          'while travelling. While connected to a public Wi-Fi network, all '
          'traffic can be securely relayed through {box_name}.'),
        box_name=_(cfg.box_name))
]

SERVER_INTERFACE = 'wg0'


class WireguardApp(app_module.App):
    """FreedomBox app for wireguard."""

    app_id = 'wireguard'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('WireGuard'),
            icon_filename='wireguard', description=_description,
            manual_page='WireGuard', clients=manifest.clients,
            tags=manifest.tags,
            donation_url='https://www.wireguard.com/donations/')
        self.add(info)

        menu_item = menu.Menu('menu-wireguard', info.name, info.icon_filename,
                              info.tags, 'wireguard:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-wireguard', info.name, icon=info.icon_filename,
            tags=info.tags, description=info.description,
            manual_page=info.manual_page,
            configure_url=reverse_lazy('wireguard:index'), login_required=True,
            clients=info.clients)
        self.add(shortcut)

        packages = Packages('packages-wireguard', ['wireguard'])
        self.add(packages)

        firewall = Firewall('firewall-wireguard', info.name,
                            ports=['wireguard-freedombox'], is_external=True)
        self.add(firewall)

    def enable(self):
        """Enable the app by simply storing a flag in key/value store."""
        from plinth import kvstore
        super().enable()
        kvstore.set('wireguard-enabled', True)
        utils.enable_connections(True)

    def disable(self):
        """Disable the app by simply storing a flag in key/value store."""
        from plinth import kvstore
        super().disable()
        kvstore.set('wireguard-enabled', False)
        utils.enable_connections(False)

    def is_enabled(self):
        """Return whether all leader components are enabled and flag is set."""
        from plinth import kvstore
        enabled = super().is_enabled()
        return enabled and kvstore.get_default('wireguard-enabled', False)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        utils.delete_connections()
        super().uninstall()
