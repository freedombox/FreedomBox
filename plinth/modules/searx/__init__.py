#
# This file is part of Plinth.
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
Plinth module to configure Searx
"""

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, frontpage
from plinth.menu import main_menu

from .manifest import clients

clients = clients

version = 1

managed_services = ['searx']

managed_packages = [
    'searx', 'uwsgi', 'uwsgi-plugin-python3', 'libapache2-mod-uwsgi'
]

name = _('Searx')

short_description = _('Web Search')

description = [
    _('Searx is a privacy-respecting internet metasearch engine. '
      'It aggregrates and displays results from multiple search engines.'),
    _('Searx can be used to avoid tracking and profiling by search engines. '
      'It stores no cookies by default. Additionally, Searx can be used over '
      'Tor for online anonymity.'),
    _('When enabled, Searx\'s web interface will be available from '
      '<a href="/searx">/searx</a>.'),
]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-search', 'searx:index',
                     short_description)

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
    helper.install(managed_packages)
    helper.call('setup', actions.superuser_run, 'searx', ['setup'])
    helper.call('post', actions.superuser_run, 'searx', ['enable'])
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut('searx', name, short_description=short_description,
                           url='/searx', login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('searx-plinth')


def enable():
    """Enable the module."""
    actions.superuser_run('searx', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('searx', ['disable'])
    frontpage.remove_shortcut('searx')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/searx/',
                                         check_certificate=False))

    return results
