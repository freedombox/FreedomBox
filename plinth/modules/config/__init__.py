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
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.names.components import DomainType
from plinth.signals import domain_added

version = 2

is_essential = True

name = _('General Configuration')

depends = ['firewall', 'names']

manual_page = 'Configure'

APACHE_CONF_ENABLED_DIR = '/etc/apache2/conf-enabled'
APACHE_HOMEPAGE_CONF_FILE_NAME = 'freedombox-apache-homepage.conf'
APACHE_HOMEPAGE_CONFIG = os.path.join(APACHE_CONF_ENABLED_DIR,
                                      APACHE_HOMEPAGE_CONF_FILE_NAME)
FREEDOMBOX_APACHE_CONFIG = os.path.join(APACHE_CONF_ENABLED_DIR,
                                        'freedombox.conf')
ADVANCED_MODE_KEY = 'advanced_mode'

app = None


class ConfigApp(app_module.App):
    """FreedomBox app for basic system configuration."""

    app_id = 'config'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-config', _('Configure'), None, 'fa-cog',
                              'config:index', parent_url_name='system')
        self.add(menu_item)

        domain_type = DomainType('domain-type-static', _('Domain Name'),
                                 'config:index', can_have_certificate=True)
        self.add(domain_type)


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


def _get_home_page_url():
    """Get the default application for the domain."""
    aug = augeas.Augeas(
        flags=augeas.Augeas.NO_LOAD + augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    conf_file = APACHE_HOMEPAGE_CONFIG if os.path.exists(
        APACHE_HOMEPAGE_CONFIG) else FREEDOMBOX_APACHE_CONFIG
    aug.set('/augeas/load/Httpd/incl[last() + 1]', conf_file)
    aug.load()

    aug.defvar('conf', '/files' + conf_file)

    for match in aug.match('/files' + conf_file +
                           '/directive["RedirectMatch"]'):
        if aug.get(match + "/arg[1]") == '''"^/$"''':
            return aug.get(match + "/arg[2]").strip('"')

    return None


def get_home_page():
    """Return the shortcut ID that is set as current home page."""
    url = _get_home_page_url()
    if url in ['/plinth/', '/plinth', 'plinth']:
        return 'plinth'

    if url == '/index.html':
        return 'apache-default'

    shortcuts = frontpage.Shortcut.list()
    for shortcut in shortcuts:
        if shortcut.url == url:
            return shortcut.component_id

    return None


def change_home_page(shortcut_id):
    """Change the FreedomBox's default redirect to URL of the shortcut
       specified.
    """
    if shortcut_id == 'plinth':
        url = '/plinth/'
    elif shortcut_id == 'apache-default':
        url = '/index.html'
    else:
        shortcuts = frontpage.Shortcut.list()
        url = [
            shortcut.url for shortcut in shortcuts
            if shortcut.component_id == shortcut_id
        ][0]

    # URL may be a reverse_lazy() proxy
    actions.superuser_run('config', ['set-home-page', str(url)])


def get_advanced_mode():
    """Get whether option is enabled."""
    from plinth import kvstore
    return kvstore.get_default(ADVANCED_MODE_KEY, False)


def set_advanced_mode(advanced_mode):
    """Turn on/off advanced mode."""
    from plinth import kvstore
    kvstore.set(ADVANCED_MODE_KEY, advanced_mode)


def init():
    """Initialize the module"""
    global app
    app = ConfigApp()
    app.set_enabled(True)

    # Register domain with Name Services module.
    domainname = get_domainname()
    if domainname:
        domain_added.send_robust(sender='config',
                                 domain_type='domain-type-static',
                                 name=domainname, services='__all__')


def setup(helper, old_version=None):
    """Install and configure the module."""
    _migrate_home_page_config()


def _migrate_home_page_config():
    """Move the home page configuration to an external file."""

    # Hold the current home page in a variable
    home_page = get_home_page()

    # Reset the home page to plinth in freedombox.conf
    actions.superuser_run('config', ['reset-home-page'])

    # Write the home page setting into the new conf file
    # This step is run at the end because it reloads the Apache server
    change_home_page(home_page)
