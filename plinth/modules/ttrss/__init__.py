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
Plinth module to configure Tiny Tiny RSS.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

title = _('News Feed Reader (Tiny Tiny RSS)')

description = [
    _('Tiny Tiny RSS is a news feed (RSS/Atom) reader and aggregator, '
      'designed to allow reading news from any location, while feeling as '
      'close to a real desktop application as possible.'),

    _('When enabled, Tiny Tiny RSS will be available from <a href="/tt-rss">'
      '/tt-rss</a> path on the web server.'),
]

service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-envelope', 'ttrss:index', 780)

    global service
    service = service_module.Service(
        'tt-rss', title, ['http', 'https'], is_external=True,
        enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'ttrss', ['pre-setup'])
    helper.install(['tt-rss', 'postgresql', 'dbconfig-pgsql', 'php-pgsql'])
    helper.call('post', actions.superuser_run, 'ttrss', ['setup'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current settings."""
    return {'enabled': is_enabled(),
            'is_running': is_running()}


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('tt-rss') and
            action_utils.webserver_is_enabled('tt-rss-plinth'))


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('tt-rss')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('ttrss', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/tt-rss', extra_options=['--no-check-certificate']))

    return results
