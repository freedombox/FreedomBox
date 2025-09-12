# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Home Assistant."""

from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.container import Container
from plinth.modules.apache.components import WebserverRoot
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_alert = '''
<div class="alert alert-warning d-flex align-items-center" role="alert">
  <div class="me-2">
    <span class="fa fa-exclamation-triangle" aria-hidden="true"></span>
    <span class="visually-hidden">{}</span>
  </div>
  <div>{}</div>
</div>
'''

_description = [
    _('Home Assistant is a home automation hub with emphasis on local control '
      'and privacy. It integrates with thousands of devices including smart '
      'bulbs, alarms, presence sensors, door bells, thermostats, irrigation '
      'timers, energy monitors, etc.'),
    _('Home Assistant can detect, configure, and use various devices on the '
      'local network. For devices using other protocols such as ZigBee, it '
      'typically requires additional hardware such as a ZigBee USB dongle. '
      'You need to re-run setup if such hardware is added or removed.'),
    _('Home Assistant web interface must be setup soon after the app is '
      'installed. An administrator account is created at this time. Home '
      'Assistant maintains its own user accounts.'),
    format_lazy(
        _('Please note that Home Assistant is installed and run inside a '
          'container provided by the Home Assistant project. Security, '
          'quality, privacy and legal reviews are done by the upstream '
          'project and not by Debian/{box_name}. Updates are performed '
          'following an independent cycle.'), box_name=_(cfg.box_name)),
    format_lazy(_alert, _('Caution:'), _('This app is experimental.')),
]


class HomeAssistnatApp(app_module.App):
    """FreedomBox app for Home Assistant."""

    app_id = 'homeassistant'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Home Assistant'),
                               icon_filename='homeassistant',
                               description=_description,
                               manual_page='HomeAssistant',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-homeassistant', info.name,
                              info.icon_filename, info.tags,
                              'homeassistant:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-homeassistant', info.name,
                                      icon=info.icon_filename, url='#',
                                      clients=info.clients, tags=info.tags,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-homeassistant', ['podman'],
                            conflicts=['libpam-tmpdir'],
                            conflicts_action=Packages.ConflictsAction.REMOVE)
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-homeassistant', [
            '/etc/apache2/includes/home-assistant-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-homeassistant', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-homeassistant', ['8123'])
        self.add(firewall_local_protection)

        webserver = WebserverRoot('webserverroot-homeassistant',
                                  'home-assistant-freedombox')
        self.add(webserver)

        image_name = 'registry.freedombox.org/' \
            'homeassistant/home-assistant:stable'
        volume_name = 'home-assistant-freedombox'
        volumes = {
            '/run/dbus': '/run/dbus',
            volume_name: '/config',
        }
        devices = {
            f'/dev/ttyUSB{number}': f'/dev/ttyUSB{number}'
            for number in range(8)
        }
        container = Container(
            'container-homeassistant', 'home-assistant-freedombox',
            image_name=image_name, volume_name=volume_name,
            volume_path='/var/lib/home-assistant-freedombox/config/',
            volumes=volumes, devices=devices, listen_ports=[(8123, 'tcp4')])
        self.add(container)

        backup_restore = BackupRestore('backup-restore-homeassistant',
                                       **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        root = self.get_component('webserverroot-homeassistant')

        def get_url():
            return f'https://{root.domain_get()}'

        url = lazy(get_url, str)()
        self.get_component('shortcut-homeassistant').url = url
        self.info.clients[0]['platforms'][0]['url'] = url

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        privileged.setup()
