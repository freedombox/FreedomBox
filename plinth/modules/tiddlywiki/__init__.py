# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for TiddlyWiki.

This is a FreedomBox-native implementation of a TiddlyWiki Nest.
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
        _('TiddlyWiki is an interactive application that runs entirely in the '
          'web browser. Each wiki is a self-contained HTML file stored on your'
          ' {box_name}. Instead of writing long wiki pages, TiddlyWiki '
          'encourages you to write several short notes called Tiddlers and '
          'link them together into a dense graph.'), box_name=_(cfg.box_name)),
    _('It is a versatile application with a wide variety of use cases - '
      'non-linear notebook, website, personal knowledge base, task and project'
      ' management system, personal diary etc. Plugins can extend the '
      'functionality of TiddlyWiki. Encrypting individual tiddlers or '
      'password-protecting a wiki file is possible from within the '
      'application.'),
    format_lazy(
        _('TiddlyWiki is downloaded from {box_name} website and not from '
          'Debian. Wikis need to be upgraded to newer version manually.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('Wikis are not public by default, but they can be downloaded for '
          'sharing or publishing. They can be edited by <a href="{users_url}">'
          'any user</a> on {box_name} belonging to the wiki group. '
          'Simultaneous editing is not supported.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index')),
    _('Create a new wiki or upload your existing wiki file to get started.')
]


class TiddlyWikiApp(app_module.App):
    """FreedomBox app for TiddlyWiki."""

    app_id = 'tiddlywiki'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'wiki': _('View and edit wiki applications')}

        info = app_module.Info(self.app_id, self._version,
                               name=_('TiddlyWiki'),
                               icon_filename='tiddlywiki',
                               short_description=_('Non-linear Notebooks'),
                               description=_description,
                               manual_page='TiddlyWiki',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-tiddlywiki', info.name,
                              info.short_description, info.icon_filename,
                              'tiddlywiki:index', parent_url_name='apps')
        self.add(menu_item)

        # The shortcut is a simple directory listing provided by Apache server.
        # Expecting a large number of wiki files, so creating a shortcut for
        # each file (like in ikiwiki's case) will crowd the front page.
        shortcut = frontpage.Shortcut(
            'shortcut-tiddlywiki', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            url='/tiddlywiki/', clients=info.clients, login_required=True,
            allowed_groups=list(groups))
        self.add(shortcut)

        dropin_configs = DropinConfigs('dropin-configs-tiddlywiki', [
            '/etc/apache2/conf-available/tiddlywiki-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-tiddlywiki', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-tiddlywiki', 'tiddlywiki-freedombox')
        self.add(webserver)

        users_and_groups = UsersAndGroups('users-and-groups-tiddlywiki',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-tiddlywiki',
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
    """List all the TiddlyWiki files."""
    return sorted([
        path.name for path in privileged.wiki_dir.iterdir()
        if path.suffix == '.html'
    ])
