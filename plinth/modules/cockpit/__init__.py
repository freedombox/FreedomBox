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
Plinth module to configure Cockpit.
"""

from django.utils.translation import ugettext_lazy as _
from plinth.utils import format_lazy

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.signals import domain_added, domain_removed, domainname_change


version = 1

managed_services = ['cockpit']

managed_packages = ['cockpit']

title = _('Dashboard of Servers \n (Cockpit)')

description = [
    _('Cockpit is an interactive server admin interface. It is easy to use '
      'and very light weight. Cockpit interacts directly with the operating '
      'system from a real linux session in a browser'),

    format_lazy(
        _('When enabled, Cockpit will be available from <a href="/cockpit">'
          '/cockpit</a> path on the web server. It can be accessed by '
          'any <a href="/plinth/sys/users">user with a {box_name} login</a>.'),
        box_name=_(cfg.box_name))
]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-dashboard', 'cockpit:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'cockpit', ['pre-setup'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'cockpit', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('cockpit', title, url='/cockpit',
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('cockpit.socket') and
            action_utils.webserver_is_enabled('cockpit-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('cockpit.socket', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('cockpit.socket', ['disable'])
    frontpage.remove_shortcut('cockpit')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/cockpit', check_certificate=False))

    return results

def on_domain_added():
    pass

def on_domain_removed():
    pass

def on_domainname_change():
    pass
