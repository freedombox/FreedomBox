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
FreedomBox app for basic system configuration.
"""

import socket

import augeas
from django.utils.translation import ugettext_lazy

from plinth import actions
from plinth.menu import main_menu
from plinth.modules import firewall
from plinth.modules.names import SERVICES
from plinth.signals import domain_added

version = 1

is_essential = True

depends = ['firewall', 'names']

manual_page = 'Configure'


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


def get_default_app():
    """Get the default application for the domain."""
    APACHE_CONFIGURATION = '/etc/apache2/conf-available/freedombox.conf'

    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    aug.set('/augeas/load/Httpd/incl[last() + 1]', APACHE_CONFIGURATION)
    aug.load()

    aug.defvar('conf', '/files' + APACHE_CONFIGURATION)

    for match in aug.match('/files' + APACHE_CONFIGURATION +
                           '/directive["RedirectMatch"]'):
        if aug.get(match + "/arg[1]") == '''"^/$"''':
            app_path = aug.get(match + "/arg[2]")

    return app_path.strip('"').strip('/')


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(
        ugettext_lazy('Configure'), 'fa-cog', 'config:index')

    # Register domain with Name Services module.
    domainname = get_domainname()
    if domainname:
        try:
            domainname_services = firewall.get_enabled_services(
                zone='external')
        except actions.ActionError:
            # This happens when firewalld is not installed.
            # TODO: Are these services actually enabled?
            domainname_services = [service[0] for service in SERVICES]
    else:
        domainname_services = None

    if domainname:
        domain_added.send_robust(sender='config', domain_type='domainname',
                                 name=domainname,
                                 description=ugettext_lazy('Domain Name'),
                                 services=domainname_services)
