# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Tor Proxy."""

import logging

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import diagnose_url
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

logger = logging.getLogger(__name__)

_description = [
    _('Tor is an anonymous communication system. You can learn more '
      'about it from the <a href="https://www.torproject.org/">Tor '
      'Project</a> website. For best protection when web surfing, the '
      'Tor Project recommends that you use the '
      '<a href="https://www.torproject.org/download/download-easy.html.en">'
      'Tor Browser</a>.'),
    format_lazy(
        _('A Tor SOCKS port is available on your {box_name} for internal '
          'networks on TCP port 9050.'), box_name=_(cfg.box_name))
]


class TorProxyApp(app_module.App):
    """FreedomBox app for Tor Proxy."""

    app_id = 'torproxy'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Tor Proxy'), icon_filename='torproxy',
                               short_description=_('Anonymity Network'),
                               description=_description,
                               manual_page='TorProxy',
                               clients=manifest.clients,
                               donation_url='https://donate.torproject.org/')
        self.add(info)

        menu_item = menu.Menu('menu-torproxy', info.name,
                              info.short_description, info.icon_filename,
                              'torproxy:index', parent_url_name='apps')
        self.add(menu_item)

        packages = Packages('packages-torproxy', [
            'tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy', 'apt-transport-tor'
        ])
        self.add(packages)

        firewall = Firewall('firewall-torproxy-socks', _('Tor Socks Proxy'),
                            ports=['tor-socks'], is_external=False)
        self.add(firewall)

        daemon = Daemon(
            'daemon-torproxy', 'tor@fbxproxy', strict_check=True,
            listen_ports=[(9050, 'tcp4'), (9050, 'tcp6'), (9040, 'tcp4'),
                          (9040, 'tcp6'), (9053, 'udp4'), (9053, 'udp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-torproxy',
                                          reserved_usernames=['debian-tor'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-torproxy',
                                       **manifest.backup)
        self.add(backup_restore)

    def disable(self):
        """Disable APT use of Tor before disabling."""
        privileged.configure(apt_transport_tor=False)
        super().disable()

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(_diagnose_url_via_tor('http://www.debian.org', '4'))
        results.append(_diagnose_url_via_tor('http://www.debian.org', '6'))
        results.append(_diagnose_tor_use('https://check.torproject.org', '4'))
        results.append(_diagnose_tor_use('https://check.torproject.org', '6'))
        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)
        if not old_version:
            logger.info('Enabling apt-transport-tor')
            privileged.configure(apt_transport_tor=True)
            logger.info('Enabling Tor Proxy app')
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


def _diagnose_url_via_tor(url, kind=None):
    """Diagnose whether a URL is reachable via Tor."""
    result = diagnose_url(url, kind=kind, wrapper='torsocks')
    result[0] = _('Access URL {url} on tcp{kind} via Tor') \
        .format(url=url, kind=kind)

    return result


def _diagnose_tor_use(url, kind=None):
    """Diagnose whether webpage at URL reports that we are using Tor."""
    expected_output = 'Congratulations. This browser is configured to use Tor.'
    result = diagnose_url(url, kind=kind, wrapper='torsocks',
                          expected_output=expected_output)
    result[0] = _('Confirm Tor usage at {url} on tcp{kind}') \
        .format(url=url, kind=kind)

    return result
