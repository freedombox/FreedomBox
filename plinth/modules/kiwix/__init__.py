# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for Kiwix content server.
"""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu, package
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.users.components import UsersAndGroups

from . import manifest, privileged

_description = [
    _('Kiwix is an offline reader for web content. It is software intended '
      'to make Wikipedia available without using the internet, but it is '
      'potentially suitable for all HTML content. Kiwix packages are in the '
      'ZIM file format.'),
    _('''Kiwix can host various kinds of content:
    <ul>
      <li>Offline versions of websites: Wikimedia projects, Stack Exchange</li>
      <li>Video content: Khan Academy, TED Talks, Crash Course</li>
      <li>Educational materials: PHET, TED Ed, Vikidia</li>
      <li>eBooks: Project Gutenberg</li>
      <li>Magazines: Low-tech Magazine</li>
    </ul>'''),
    _('You can <a href="https://library.kiwix.org" target="_blank" '
      'rel="noopener noreferrer">download</a> content packages from the Kiwix '
      'project or <a href="https://openzim.org/wiki/Build_your_ZIM_file" '
      'target="_blank" rel="noopener noreferrer">create</a> your own.'),
]


class KiwixApp(app_module.App):
    """FreedomBox app for Kiwix."""

    app_id = 'kiwix'

    _version = 1

    DAEMON = 'kiwix-server-freedombox'

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        groups = {'kiwix': _('Manage Kiwix content server')}

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Kiwix'),
            icon_filename='kiwix', short_description=_('Offline Wikipedia'),
            description=_description, manual_page='Kiwix',
            clients=manifest.clients,
            donation_url='https://www.kiwix.org/en/support-us/')
        self.add(info)

        menu_item = menu.Menu('menu-kiwix', info.name, info.short_description,
                              info.icon_filename, 'kiwix:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-kiwix', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/kiwix',
                                      clients=info.clients,
                                      login_required=False,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = package.Packages('packages-kiwix', ['kiwix-tools'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-kiwix', [
            '/etc/apache2/conf-available/kiwix-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-kiwix', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-kiwix', ['4201'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-kiwix', 'kiwix-freedombox',
                              urls=['https://{host}/kiwix'])
        self.add(webserver)

        daemon = Daemon('daemon-kiwix', self.DAEMON,
                        listen_ports=[(4201, 'tcp4')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-kiwix',
                                          reserved_usernames=['kiwix'],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-kiwix',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version=None):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


def validate_file_name(file_name: str):
    """Check if the content package file has a valid extension."""
    if not file_name.endswith('.zim'):
        raise ValueError(f'Expected a ZIM file. Found {file_name}')
