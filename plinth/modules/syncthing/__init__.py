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

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.utils import format_lazy


version = 1

depends = ['apps']

managed_services = ['syncthing']

managed_packages = ['syncthing']

title = _('File Synchronization (Syncthing)')

description = [
    _('Syncthing is an application that can synchronizes files across '
      'multiple devices.  Creation, modification and deletion of files on one '
      'device will automatically be replicated to other devices.'),
    format_lazy(
        _('Running Synching on {box_name}, provides an extra synchronization '
          'point for your data that is available most of the time so that '
          'your devices synchronize more often.  On {box_name}, a single '
          'instance of Syncthing runs and may be used by many users.  Each '
          'user\'s set of devices many be synchronized with a distinct set '
          'of folders.  Web interface is only available for users '
          'belonging to the "admin" group.'), box_name=_(cfg.box_name)),
    _('When enabled, Syncthing will be available from <a href="/syncthing/">'
      '/syncthing</a> web interface. Desktop and mobile clients are also '
      '<a href="https://syncthing.net/">available.</a>'),
]

service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-refresh', 'syncthing:index')

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
            disable=disable,
            is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'syncthing', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut(
        'syncthing', title, url='/syncthing/', login_required=True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('syncthing@syncthing')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('syncthing@syncthing') and
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
