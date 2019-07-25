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

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import names
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.signals import domain_added, domain_removed, domainname_change
from plinth.utils import format_lazy

from .manifest import backup, clients # noqa, pylint: disable=unused-import

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

manual_page = 'Cockpit'

app = None


class CockpitApp(app_module.App):
    """FreedomBox app for Cockpit."""

    app_id = 'cockpit'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-cockpit', name, short_description,
                              'fa-wrench', 'cockpit:index',
                              parent_url_name='system')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-cockpit', name,
                                      short_description=short_description,
                                      icon='cockpit', url='/_cockpit/',
                                      clients=clients, login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-cockpit', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-cockpit', 'cockpit-freedombox')
        self.add(webserver)

        daemon = Daemon('daemon-cockpit', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the module."""
    global app
    app = CockpitApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)

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
    helper.call('post', app.enable)


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
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        actions.superuser_run('cockpit', ['add-domain', name])


def on_domain_removed(sender, domain_type, name, **kwargs):
    """Handle removal of a domain."""
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        actions.superuser_run('cockpit', ['remove-domain', name])


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Handle change of a domain."""
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        actions.superuser_run('cockpit', ['remove-domain', old_domainname])
        actions.superuser_run('cockpit', ['add-domain', new_domainname])
