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
Plinth module to configure ownCloud
"""

from django.utils.translation import ugettext_lazy as _
from functools import partial
import os

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module

version = 1

depends = ['apps']

managed_packages = ['postgresql', 'php5-pgsql', 'owncloud', 'php-dropbox',
                    'php-google-api-php-client']

title = _('File Hosting (ownCloud)')

description = [
    _('ownCloud gives you universal access to your files through a web '
      'interface or WebDAV. It also provides a platform to easily view '
      '& sync your contacts, calendars and bookmarks across all your '
      'devices and enables basic editing right on the web. Installation '
      'has minimal server requirements, doesn\'t need special '
      'permissions and is quick. ownCloud is extendable via a simple '
      'but powerful API for applications and plugins.'),

    _('When enabled, the ownCloud installation will be available '
      'from <a href="/owncloud">/owncloud</a> path on the web server. '
      'Visit this URL to set up the initial administration account for '
      'ownCloud.')
]

service = None


def init():
    """Initialize the ownCloud module"""
    # XXX: ownCloud has been removed from Debian
    if not os.path.isfile('/etc/owncloud/config.php') and \
       not os.path.isfile('/etc/owncloud/autoconfig.php'):
        return

    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-picture', 'owncloud:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'owncloud', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=_enable, disable=_disable)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'owncloud-setup', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            'owncloud', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=_enable, disable=_disable)
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Return the current status"""
    return {'enabled': is_enabled()}


def is_enabled():
    """Return whether the module is enabled."""
    output = actions.run('owncloud-setup', ['status'])
    return 'enable' in output.split()


def enable(should_enable):
    """Enable/disable the module."""
    option = 'enable' if should_enable else 'noenable'
    actions.superuser_run('owncloud-setup', [option])

    # Send a signal to other modules that the service is
    # enabled/disabled
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/owncloud', check_certificate=False))

    return results


_enable = partial(enable, True)
_disable = partial(enable, False)
