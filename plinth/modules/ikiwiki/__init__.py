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
Plinth module to configure ikiwiki
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

title = _('Wiki and Blog (ikiwiki)')

description = [
    _('When enabled, the blogs and wikis will be available '
      'from <a href="/ikiwiki">/ikiwiki</a>.')
]

service = None


def init():
    """Initialize the ikiwiki module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-edit', 'ikiwiki:index', 1100)

    global service
    service = service_module.Service(
        'ikiwiki', title, ['http', 'https'], is_external=True,
        enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['ikiwiki',
                    'gcc',
                    'libc6-dev',
                    'libtimedate-perl',
                    'libcgi-formbuilder-perl',
                    'libcgi-session-perl',
                    'libxml-writer-perl'])
    helper.call('post', actions.superuser_run, 'ikiwiki', ['setup'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current setting."""
    return {'enabled': is_enabled()}


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('ikiwiki-plinth')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('ikiwiki', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/ikiwiki', extra_options=['--no-check-certificate']))

    return results
