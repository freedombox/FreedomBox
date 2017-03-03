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
Plinth module to configure gnu-social
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module


version = 1

depends = ['apps']

managed_packages = ['gnu-social']

service = None

title = _('GNU Social (gnusocial)')

description = [
    _('gnusocial is a social networking website like twitter'
      '<a href="/gnu-social">/gnusocial</a>.')
]


def init():
    """Initialize the gnu-social module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-edit', 'gnusocial:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'gnu-social', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            add_shortcuts()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'gnusocial', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'gnusocial', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            'gnu-social', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcuts)


def add_shortcuts():
        frontpage.add_shortcut(
            'gnusocial' ,title, url='/gnu-social/',
            login_required=True, icon='gnu-social')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('gnu-social')


def enable():
    """Enable the module."""
    actions.superuser_run('gnu-social', ['enable'])
    add_shortcuts()


def disable():
    """Enable the module."""
    actions.superuser_run('gnu-social', ['disable'])
    frontpage.remove_shortcut('gnusocial*')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/gnu-social', check_certificate=False))

    return results
