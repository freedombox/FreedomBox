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
FreedomBox app for Apache server.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.utils import format_lazy

version = 7

is_essential = True

managed_services = ['apache2']

managed_packages = ['apache2', 'php-fpm']

app = None


class ApacheApp(app_module.App):
    """FreedomBox app for Apache web server."""

    app_id = 'apache'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        web_server_ports = Firewall('firewall-web', _('Web Server'),
                                    ports=['http', 'https'], is_external=True)
        self.add(web_server_ports)

        freedombox_ports = Firewall(
            'firewall-plinth',
            format_lazy(
                _('{box_name} Web Interface (Plinth)'), box_name=_(
                    cfg.box_name)), ports=['http', 'https'], is_external=True)
        self.add(freedombox_ports)

        letsencrypt = LetsEncrypt('letsencrypt-apache', domains='*',
                                  daemons=[managed_services[0]])
        self.add(letsencrypt)

        daemon = Daemon('daemon-apache', managed_services[0])
        self.add(daemon)


def init():
    """Initailze firewall module"""
    global app
    app = ApacheApp()
    app.set_enabled(True)


def setup(helper, old_version=None):
    """Configure the module."""
    helper.install(managed_packages)
    actions.superuser_run(
        'apache',
        ['setup', '--old-version', str(old_version)])
