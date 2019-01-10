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
FreedomBox app to configure Cockpit.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.modules import names
from plinth.signals import domain_added, domain_removed, domainname_change
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_services = ['cockpit.socket']

managed_packages = ['cockpit']

name = _('Cockpit')

short_description = _('Server Administration')

description = [
    format_lazy(
        _('Cockpit is a server manager that makes it easy to administer '
          'GNU/Linux servers via a web browser. On a {box_name}, controls '
          'are available for many advanced functions that are not usually '
          'required. A web based terminal for console operations is also '
          'available.'), box_name=_(cfg.box_name)),
    format_lazy(
        _('When enabled, Cockpit will be available from <a href="/_cockpit/">'
          '/_cockpit/</a> path on the web server. It can be accessed by '
          '<a href="{users_url}">any user</a> on {box_name} belonging to '
          'the admin group.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index')),
]

service = None

manual_page = 'Cockpit'


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-wrench', 'cockpit:index',
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

    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)
    domainname_change.connect(on_domainname_change)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    domains = [
        domain for domains_of_a_type in names.domains.values()
        for domain in domains_of_a_type
    ]
    helper.call('post', actions.superuser_run, 'cockpit', ['setup'] + domains)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Add a shortcut the frontpage."""
    frontpage.add_shortcut('cockpit', name,
                           short_description=short_description,
                           url='/_cockpit/', login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('cockpit-freedombox')
            and action_utils.service_is_running('cockpit.socket'))


def enable():
    """Enable the module."""
    actions.superuser_run('cockpit', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('cockpit', ['disable'])
    frontpage.remove_shortcut('cockpit')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/_cockpit/',
                                         check_certificate=False))

    return results


def on_domain_added(sender, domain_type, name, description='', services=None,
                    **kwargs):
    """Handle addition of a new domain."""
    actions.superuser_run('cockpit', ['add-domain', name])


def on_domain_removed(sender, domain_type, name, **kwargs):
    """Handle removal of a domain."""
    actions.superuser_run('cockpit', ['remove-domain', name])


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Handle change of a domain."""
    actions.superuser_run('cockpit', ['remove-domain', old_domainname])
    actions.superuser_run('cockpit', ['add-domain', new_domainname])
