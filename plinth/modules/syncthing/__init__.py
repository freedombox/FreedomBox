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
Plinth module to configure Syncthing.
"""

import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module

version = 1

depends = ['apps']

managed_services = ['syncthing']

managed_packages = ['syncthing']

title = _('Personal Cloud (Syncthing)')

description = [
    _('Syncthing is a file synchronization program that can sync files '
      'between multiple devices. Syncthing enables this FreedomBox to be '
      'used as a cloud server for storing and sharing files'),
    _('When enabled, Syncthing will be available from <a href="/syncthing/">'
      '/syncthing</a> path on the web server.'),
]

service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-cloud', 'syncthing:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'syncthing', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut(
        'syncthing', title, url='/syncthing/', login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('syncthing@plinth.service') and
            action_utils.webserver_is_enabled('syncthing-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('syncthing', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('syncthing', ['disable'])
    frontpage.remove_shortcut('syncthing')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all(
            'https://{host}/syncthing/', check_certificate=False))

    return results
