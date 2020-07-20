# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure MediaWiki.
"""

import re

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 8

managed_packages = ['mediawiki', 'imagemagick', 'php-sqlite3']

managed_services = ['mediawiki-jobrunner']

_description = [
    _('MediaWiki is the wiki engine that powers Wikipedia and other WikiMedia '
      'projects. A wiki engine is a program for creating a collaboratively '
      'edited website. You can use MediaWiki to host a wiki-like website, '
      'take notes or collaborate with friends on projects.'),
    _('This MediaWiki instance comes with a randomly generated administrator '
      'password. You can set a new password in the "Configuration" section '
      'and log in using the "admin" account. You can then create more user '
      'accounts from MediaWiki itself by going to the <a '
      'href="/mediawiki/index.php/Special:CreateAccount">'
      'Special:CreateAccount</a> page.'),
    _('Anyone with a link to this wiki can read it. Only users that are '
      'logged in can make changes to the content.')
]

app = None


class MediaWikiApp(app_module.App):
    """FreedomBox app for MediaWiki."""

    app_id = 'mediawiki'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        self._private_mode = True

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('MediaWiki'), icon_filename='mediawiki',
                               short_description=_('Wiki'),
                               description=_description,
                               manual_page='MediaWiki', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-mediawiki', info.name,
                              info.short_description, info.icon_filename,
                              'mediawiki:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = Shortcut('shortcut-mediawiki', info.name,
                            short_description=info.short_description,
                            icon=info.icon_filename, url='/mediawiki',
                            clients=info.clients, login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-mediawiki', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-mediawiki', 'mediawiki',
                              urls=['https://{host}/mediawiki'])
        self.add(webserver)

        webserver = Webserver('webserver-mediawiki-freedombox',
                              'mediawiki-freedombox')
        self.add(webserver)

        daemon = Daemon('daemon-mediawiki', managed_services[0])
        self.add(daemon)


class Shortcut(frontpage.Shortcut):
    """Frontpage shortcut for only logged users when in private mode."""

    def enable(self):
        """When enabled, check if MediaWiki is in private mode."""
        super().enable()
        self.login_required = is_private_mode_enabled()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('setup', actions.superuser_run, 'mediawiki', ['setup'])
    helper.call('update', actions.superuser_run, 'mediawiki', ['update'])
    helper.call('post', app.enable)


def is_public_registration_enabled():
    """Return whether public registration is enabled."""
    output = actions.superuser_run('mediawiki',
                                   ['public-registrations', 'status'])
    return output.strip() == 'enabled'


def is_private_mode_enabled():
    """ Return whether private mode is enabled or disabled"""
    output = actions.superuser_run('mediawiki', ['private-mode', 'status'])
    return output.strip() == 'enabled'


def get_default_skin():
    """Return the value of the default skin"""

    def _find_skin(config_file):
        with open(config_file, 'r') as config:
            for line in config:
                if line.startswith('$wgDefaultSkin'):
                    return re.findall(r'["\'][^"\']*["\']',
                                      line)[0].strip('"\'')

        return None

    user_config = '/etc/mediawiki/FreedomBoxSettings.php'
    static_config = '/etc/mediawiki/FreedomBoxStaticSettings.php'

    return _find_skin(user_config) or _find_skin(static_config)
