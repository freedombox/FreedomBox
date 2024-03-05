# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Privoxy.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import action_utils
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import diagnose_url
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Privoxy is a non-caching web proxy with advanced filtering '
      'capabilities for enhancing privacy, modifying web page data and '
      'HTTP headers, controlling access, and removing ads and other '
      'obnoxious Internet junk. '),
    format_lazy(
        _('You can use Privoxy by modifying your browser proxy settings to '
          'your {box_name} hostname (or IP address) with port 8118. Only '
          'connections from local network IP addresses are permitted. '
          'While using Privoxy, you can see its configuration details and '
          'documentation at '
          '<a href="http://config.privoxy.org">http://config.privoxy.org/</a> '
          'or <a href="http://p.p">http://p.p</a>.'),
        box_name=_(cfg.box_name)),
]


class PrivoxyApp(app_module.App):
    """FreedomBox app for Privoxy."""

    app_id = 'privoxy'

    _version = 2

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Privoxy'),
            icon_filename='privoxy', short_description=_('Web Proxy'),
            description=_description, manual_page='Privoxy',
            donation_url='https://www.privoxy.org/faq/general.html#DONATE')
        self.add(info)

        menu_item = menu.Menu('menu-privoxy', info.name,
                              info.short_description, info.icon_filename,
                              'privoxy:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-privoxy', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('privoxy:index'), login_required=True)
        self.add(shortcut)

        packages = Packages('packages-privoxy', ['privoxy'])
        self.add(packages)

        firewall = Firewall('firewall-privoxy', info.name, ports=['privoxy'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-privoxy', 'privoxy',
                        listen_ports=[(8118, 'tcp4'), (8118, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-privoxy',
                                          reserved_usernames=['privoxy'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-privoxy',
                                       **manifest.backup)
        self.add(backup_restore)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(diagnose_url('https://www.debian.org'))
        results.extend(diagnose_url_with_proxy())
        return results

    def setup(self, old_version):
        """Install and configure the app."""
        privileged.pre_install()
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()


def diagnose_url_with_proxy():
    """Run a diagnostic on a URL with a proxy."""
    url = 'https://debian.org/'  # Gives a simple redirect to www.

    results = []
    for address in action_utils.get_addresses():
        proxy = 'http://{host}:8118/'.format(host=address['url_address'])
        env = {'https_proxy': proxy}

        result = diagnose_url(url, kind=address['kind'], env=env)
        result.check_id = f'privoxy-url-proxy-kind-{url}-{address["kind"]}'
        result.description = gettext_noop(
            'Access {url} with proxy {proxy} on tcp{kind}')
        result.parameters['proxy'] = proxy
        results.append(result)

    return results
