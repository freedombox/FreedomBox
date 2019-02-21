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

import os
import socket

import augeas
from django.utils.translation import ugettext_lazy

from plinth import actions
from plinth.menu import main_menu
from plinth.modules import firewall
from plinth.modules.names import SERVICES
from plinth.signals import domain_added

version = 2

is_essential = True

depends = ['firewall', 'names']

manual_page = 'Configure'

APACHE_CONF_ENABLED_DIR = '/etc/apache2/conf-enabled'
APACHE_HOMEPAGE_CONF_FILE_NAME = 'freedombox-apache-homepage.conf'
APACHE_HOMEPAGE_CONFIG = os.path.join(APACHE_CONF_ENABLED_DIR,
                                      APACHE_HOMEPAGE_CONF_FILE_NAME)
FREEDOMBOX_APACHE_CONFIG = os.path.join(APACHE_CONF_ENABLED_DIR,
                                        'freedombox.conf')


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


def get_home_page():
    """Get the default application for the domain."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    conf_file = APACHE_HOMEPAGE_CONFIG if os.path.exists(
        APACHE_HOMEPAGE_CONFIG) else FREEDOMBOX_APACHE_CONFIG
    aug.set('/augeas/load/Httpd/incl[last() + 1]', conf_file)
    aug.load()

    aug.defvar('conf', '/files' + conf_file)

    app_path = 'plinth'

    for match in aug.match('/files' + conf_file +
                           '/directive["RedirectMatch"]'):
        if aug.get(match + "/arg[1]") == '''"^/$"''':
            app_path = aug.get(match + "/arg[2]")

    # match this against the app_id in the entries of frontpage.get_shortcuts()
    # The underscore is to handle Ikiwiki app_ids
    app = app_path.strip('/"').replace('/', '_')
    if app == 'index.html':
        return 'apache-default'
    elif app.endswith('jsxc'):
        return 'jsxc'
    else:
        return app


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(ugettext_lazy('Configure'), 'fa-cog', 'config:index')

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


def setup(helper, old_version=None):
    """Install and configure the module."""
    _migrate_home_page_config()


def _migrate_home_page_config():
    """Move the home page configuration to an external file."""

    # Hold the current default app in a variable
    home_page_path = get_home_page().replace('_', '/')

    # Write the default app setting into the new conf file
    # This step is run at the end because it reloads the Apache server
    actions.superuser_run('config', ['set-home-page', home_page_path])
