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
FreedomBox app to configure Searx.
"""

import os

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, frontpage
from plinth.menu import main_menu
from plinth.modules.users import register_group

from .manifest import backup, clients

clients = clients

version = 2

managed_services = ['searx']

managed_packages = ['searx', 'uwsgi', 'uwsgi-plugin-python3']

name = _('Searx')

short_description = _('Web Search')

description = [
    _('Searx is a privacy-respecting Internet metasearch engine. '
      'It aggregrates and displays results from multiple search engines.'),
    _('Searx can be used to avoid tracking and profiling by search engines. '
      'It stores no cookies by default.')
]

group = ('web-search', _('Search the web'))

service = None

manual_page = 'Searx'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'searx', 'searx:index',
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
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'searx', ['setup'])
    if not old_version:
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
                           url='/searx/', login_required=True, allowed_groups=[group[0]])


def get_safe_search_setting():
    """Get the current value of the safe search setting for Seax."""
    value = actions.superuser_run('searx', ['get-safe-search'])
    return int(value.strip())


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('searx-freedombox')
            and os.path.exists('/etc/uwsgi/apps-enabled/searx.ini'))


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
