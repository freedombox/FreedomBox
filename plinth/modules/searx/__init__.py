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

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth import service as service_module
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group

from .manifest import PUBLIC_ACCESS_SETTING_FILE, backup, clients

clients = clients

version = 3

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

app = None


class SearxApp(app_module.App):
    """FreedomBox app for Searx."""

    app_id = 'searx'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-searx', name, short_description, 'searx',
                              'searx:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-searx', name, short_description=short_description,
            icon='searx', url='/searx/', clients=clients,
            login_required=(not is_public_access_enabled()),
            allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-searx', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-searx', 'searx-freedombox')
        self.add(webserver)

        webserver = SearxWebserverAuth('webserver-searx-auth',
                                       'searx-freedombox-auth')
        self.add(webserver)

        uwsgi = Uwsgi('uwsgi-searx', 'searx')
        self.add(uwsgi)

    def set_shortcut_login_required(self, login_required):
        """Change the login_required property of shortcut."""
        shortcut = self.remove('shortcut-searx')
        shortcut.login_required = login_required
        self.add(shortcut)


class SearxWebserverAuth(Webserver):
    """Component to handle Searx authentication webserver configuration."""

    def is_enabled(self):
        """Return if configuration is enabled or public access is enabled."""
        return is_public_access_enabled() or super().is_enabled()

    def enable(self):
        """Enable apache configuration only if public access is disabled."""
        if not is_public_access_enabled():
            super().enable()


def init():
    """Intialize the module."""
    global app
    app = SearxApp()
    register_group(group)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)

        if is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'searx', ['setup'])
    if not old_version or old_version < 3:
        helper.call('post', actions.superuser_run, 'searx', ['enable'])
        helper.call('post', actions.superuser_run, 'searx',
                    ['disable-public-access'])
        app.set_shortcut_login_required(True)
        app.enable()

    global service
    if service is None:
        service = service_module.Service(managed_services[0], name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', app.enable)


def get_safe_search_setting():
    """Get the current value of the safe search setting for Searx."""
    value = actions.superuser_run('searx', ['get-safe-search'])
    return int(value.strip())


def is_public_access_enabled():
    """Check whether public access is enabled for Searx."""
    return os.path.exists(PUBLIC_ACCESS_SETTING_FILE)


def is_enabled():
    """Return whether the module is enabled."""
    return app.is_enabled()


def enable():
    """Enable the module."""
    app.enable()


def disable():
    """Disable the module."""
    app.disable()


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/searx/',
                                         check_certificate=False))

    return results


def enable_public_access():
    """Allow Searx app to be accessed by anyone with access."""
    actions.superuser_run('searx', ['enable-public-access'])
    app.get_component('webserver-searx-auth').disable()
    app.set_shortcut_login_required(False)


def disable_public_access():
    """Allow Searx app to be accessed by logged-in users only."""
    actions.superuser_run('searx', ['disable-public-access'])
    app.get_component('webserver-searx-auth').enable()
    app.set_shortcut_login_required(True)
