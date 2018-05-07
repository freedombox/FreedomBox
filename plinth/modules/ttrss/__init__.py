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

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, cfg, frontpage
from plinth.menu import main_menu
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import clients

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
          'any <a href="/plinth/sys/users">user with a {box_name} login</a>.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('When using a mobile or desktop application for Tiny Tiny RSS, use '
          'the URL <a href="/tt-rss-app/">/tt-rss-app</a> for connecting.'))
]

clients = clients

group = ('feed-reader', _('Read and subscribe to news feeds'))

service = None

manual_page = 'TinyTinyRSS'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-envelope', 'ttrss:index',
                     short_description)
    register_group(group)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'ttrss', ['pre-setup'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ttrss', ['setup'])
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Add a shortcut to the front page."""
    frontpage.add_shortcut('ttrss', name, short_description=short_description,
                           url='/tt-rss', login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('tt-rss')
            and action_utils.webserver_is_enabled('tt-rss-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('ttrss', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('ttrss', ['disable'])
    frontpage.remove_shortcut('ttrss')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/tt-rss',
                                         check_certificate=False))

    return results
