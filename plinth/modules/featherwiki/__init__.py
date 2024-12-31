# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for Feather Wiki.

This is a FreedomBox-native implementation of a Feather Wiki Nest.
This app doesn't install any Debian packages.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('Feather Wiki is a tool to create simple self-contained wikis, each '
          'stored in a single HTML file on your {box_name}. You can use it as '
          'a personal wiki, as a web notebook, or for project documentation.'),
        box_name=_(cfg.box_name)),
    _('Each wiki is a small file. Create as many wikis as you like, such as '
      'one wiki per topic. Customize each wiki to your liking with extensions '
      'and other customization options.'),
    format_lazy(
        _('Feather Wiki is downloaded from {box_name} website and not from '
          'Debian. Wikis need to be upgraded to newer version manually.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('Wikis are not public by default, but they can be downloaded for '
          'sharing or publishing. They can be edited by <a href="{users_url}">'
          'any user</a> on {box_name} belonging to the wiki group. '
          'Simultaneous editing is not supported.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index'))
]


class FeatherWikiApp(app_module.App):
    """FreedomBox app for Feather Wiki."""

    app_id = 'featherwiki'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'wiki': _('View and edit wiki applications')}

        info = app_module.Info(self.app_id, self._version,
                               name=_('Feather Wiki'),
                               icon_filename='featherwiki',
                               description=_description,
                               manual_page='FeatherWiki',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-featherwiki', info.name,
                              info.icon_filename, info.tags,
                              'featherwiki:index', parent_url_name='apps')
        self.add(menu_item)

        # The shortcut is a simple directory listing provided by Apache server.
        # Expecting a large number of wiki files, so creating a shortcut for
        # each file (like in ikiwiki's case) will crowd the front page.
        shortcut = frontpage.Shortcut(
            'shortcut-featherwiki', info.name, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            url='/featherwiki/', clients=info.clients, tags=info.tags,
            login_required=True, allowed_groups=list(groups))
        self.add(shortcut)

        dropin_configs = DropinConfigs('dropin-configs-featherwiki', [
            '/etc/apache2/conf-available/featherwiki-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-featherwiki', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-featherwiki',
                              'featherwiki-freedombox')
        self.add(webserver)

        users_and_groups = UsersAndGroups('users-and-groups-featherwiki',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-featherwiki',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version=None):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

    def uninstall(self):
        """Purge directory with all the wikis."""
        super().uninstall()
        privileged.uninstall()


def get_wiki_list():
    """List all the Feather Wiki files."""
    return sorted([
        path.name for path in privileged.wiki_dir.iterdir()
        if path.suffix == '.html'
    ])
