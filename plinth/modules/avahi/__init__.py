# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for service discovery."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.config import get_hostname
from plinth.modules.firewall.components import Firewall
from plinth.modules.names.components import DomainType
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.signals import domain_added, domain_removed, post_hostname_change
from plinth.utils import format_lazy

from . import manifest

# pylint: disable=C0103

_description = [
    format_lazy(
        _('Service discovery allows other devices on the network to '
          'discover your {box_name} and services running on it.  It '
          'also allows {box_name} to discover other devices and '
          'services running on your local network.  Service discovery is '
          'not essential and works only on internal networks.  It may be '
          'disabled to improve security especially when connecting to a '
          'hostile local network.'), box_name=_(cfg.box_name))
]


class AvahiApp(app_module.App):
    """FreedomBox app for Avahi."""

    app_id = 'avahi'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, depends=['names'],
                               name=_('Service Discovery'), icon='fa-compass',
                               description=_description,
                               manual_page='ServiceDiscovery')
        self.add(info)

        menu_item = menu.Menu('menu-avahi', info.name, None, info.icon,
                              'avahi:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-avahi', ['avahi-daemon', 'avahi-utils'])
        self.add(packages)

        domain_type = DomainType('domain-type-local',
                                 _('Local Network Domain'), 'config:index',
                                 can_have_certificate=False)
        self.add(domain_type)

        firewall = Firewall('firewall-avahi', info.name, ports=['mdns'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-avahi', 'avahi-daemon')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-avahi',
                                       **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        if self.is_enabled():
            domain_added.send_robust(sender='avahi',
                                     domain_type='domain-type-local',
                                     name=get_hostname() + '.local',
                                     services='__all__')

        post_hostname_change.connect(on_post_hostname_change)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        # Reload avahi-daemon now that first-run does not reboot. After
        # performing FreedomBox Service (Plinth) package installation, new
        # Avahi files will be available and require restart.
        service_privileged.reload('avahi-daemon')
        self.enable()


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """Update .local domain after hostname change."""
    del sender  # Unused
    del kwargs  # Unused

    domain_removed.send_robust(sender='avahi', domain_type='domain-type-local',
                               name=old_hostname + '.local')
    domain_added.send_robust(sender='avahi', domain_type='domain-type-local',
                             name=new_hostname + '.local', services='__all__')
