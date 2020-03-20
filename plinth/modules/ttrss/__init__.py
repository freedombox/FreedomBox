# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Tiny Tiny RSS.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.utils import Version, format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 3

managed_services = ['tt-rss']

managed_packages = [
    'tt-rss', 'postgresql', 'dbconfig-pgsql', 'php-pgsql', 'python3-psycopg2'
]

_description = [
    _('Tiny Tiny RSS is a news feed (RSS/Atom) reader and aggregator, '
      'designed to allow reading news from any location, while feeling as '
      'close to a real desktop application as possible.'),
    format_lazy(
        _('When enabled, Tiny Tiny RSS can be accessed by any '
          '<a href="{users_url}">user with a {box_name} login</a>.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index')),
    format_lazy(
        _('When using a mobile or desktop application for Tiny Tiny RSS, use '
          'the URL <a href="/tt-rss-app/" data-turbolinks="false">'
          '/tt-rss-app</a> for connecting.'))
]

app = None


class TTRSSApp(app_module.App):
    """FreedomBox app for TT-RSS."""

    app_id = 'ttrss'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'feed-reader': _('Read and subscribe to news feeds')}

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Tiny Tiny RSS'), icon_filename='ttrss',
                               short_description=_('News Feed Reader'),
                               description=_description,
                               manual_page='TinyTinyRSS', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-ttrss', info.name, info.short_description,
                              info.icon_filename, 'ttrss:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-ttrss', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/tt-rss',
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        firewall = Firewall('firewall-ttrss', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-ttrss', 'tt-rss-plinth',
                              urls=['https://{host}/tt-rss'])
        self.add(webserver)

        daemon = Daemon('daemon-ttrss', managed_services[0])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-ttrss',
                                          groups=groups)
        self.add(users_and_groups)

    def enable(self):
        """Enable components and API access."""
        super().enable()
        actions.superuser_run('ttrss', ['enable-api-access'])


def init():
    """Initialize the module."""
    global app
    app = TTRSSApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'ttrss', ['pre-setup'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ttrss', ['setup'])
    helper.call('post', app.enable)


def force_upgrade(helper, packages):
    """Force update package to resolve conffile prompts."""
    if 'tt-rss' not in packages:
        return False

    # Allow tt-rss any lower version to upgrade to 19.8.*
    package = packages['tt-rss']
    if Version(package['new_version']) > Version('19.9~'):
        return False

    helper.install(['tt-rss'], force_configuration='new')
    actions.superuser_run('ttrss', ['setup'])
    return True


def backup_pre(packet):
    """Save database contents."""
    actions.superuser_run('ttrss', ['dump-database'])


def restore_post(packet):
    """Restore database contents."""
    actions.superuser_run('ttrss', ['restore-database'])
