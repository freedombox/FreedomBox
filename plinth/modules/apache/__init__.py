# SPDX-License-Identifier: AGPL-3.0-or-later
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

version = 8

is_essential = True

managed_services = ['apache2']

managed_packages = ['apache2', 'php-fpm', 'ssl-cert']

app = None


class ApacheApp(app_module.App):
    """FreedomBox app for Apache web server."""

    app_id = 'apache'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential)
        self.add(info)

        web_server_ports = Firewall('firewall-web', _('Web Server'),
                                    ports=['http', 'https'], is_external=True)
        self.add(web_server_ports)

        freedombox_ports = Firewall(
            'firewall-plinth',
            format_lazy(_('{box_name} Web Interface (Plinth)'),
                        box_name=_(cfg.box_name)), ports=['http', 'https'],
            is_external=True)
        self.add(freedombox_ports)

        letsencrypt = LetsEncrypt('letsencrypt-apache', domains='*',
                                  daemons=[managed_services[0]])
        self.add(letsencrypt)

        daemon = Daemon('daemon-apache', managed_services[0])
        self.add(daemon)


def setup(helper, old_version=None):
    """Configure the module."""
    helper.install(managed_packages)
    actions.superuser_run(
        'apache',
        ['setup', '--old-version', str(old_version)])
