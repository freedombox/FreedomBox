#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to configure Tiny Tiny RSS.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import Version, format_lazy

from .manifest import backup, clients

version = 3

managed_services = ['tt-rss']

managed_packages = [
    'tt-rss', 'postgresql', 'dbconfig-pgsql', 'php-pgsql', 'python3-psycopg2'
]

name = _('Tiny Tiny RSS')

short_description = _('News Feed Reader')

description = [
    _('Tiny Tiny RSS is a news feed (RSS/Atom) reader and aggregator, '
      'designed to allow reading news from any location, while feeling as '
      'close to a real desktop application as possible.'),
    format_lazy(
        _('When enabled, Tiny Tiny RSS will be available from <a href="/tt-'
          'rss">/tt-rss</a> path on the web server. It can be accessed by '
          'any <a href="{users_url}">user with a {box_name} login</a>.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index')),
    format_lazy(
        _('When using a mobile or desktop application for Tiny Tiny RSS, use '
          'the URL <a href="/tt-rss-app/">/tt-rss-app</a> for connecting.'))
]

clients = clients

group = ('feed-reader', _('Read and subscribe to news feeds'))

manual_page = 'TinyTinyRSS'

app = None


class TTRSSApp(app_module.App):
    """FreedomBox app for TT-RSS."""

    app_id = 'ttrss'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-ttrss', name, short_description, 'ttrss',
                              'ttrss:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-ttrss', name, short_description=short_description,
            icon='ttrss', url='/tt-rss', clients=clients, login_required=True,
            allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-ttrss', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-ttrss', 'tt-rss-plinth')
        self.add(webserver)

        daemon = Daemon('daemon-ttrss', managed_services[0])
        self.add(daemon)

    def enable(self):
        """Enable components and API access."""
        super().enable()
        actions.superuser_run('ttrss', ['enable-api-access'])


def init():
    """Initialize the module."""
    global app
    app = TTRSSApp()
    register_group(group)

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
        return

    # tt-rss 17.4 -> 18.12
    package = packages['tt-rss']
    if Version(package['current_version']) >= Version('18.12') or \
       Version(package['new_version']) < Version('18.12'):
        return

    helper.install(['tt-rss'], force_configuration='new')
    actions.superuser_run('ttrss', ['setup'])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/tt-rss',
                                         check_certificate=False))

    return results


def backup_pre(packet):
    """Save database contents."""
    actions.superuser_run('ttrss', ['dump-database'])


def restore_post(packet):
    """Restore database contents."""
    actions.superuser_run('ttrss', ['restore-database'])
