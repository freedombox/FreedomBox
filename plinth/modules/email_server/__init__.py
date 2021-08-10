"""FreedomBox email server app"""
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

import plinth.app
import plinth.daemon
import plinth.frontpage
import plinth.menu
from plinth import actions
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from . import audit
from . import manifest

version = 1

packages = [
    'postfix-ldap', 'dovecot-pop3d', 'dovecot-imapd',
    'dovecot-ldap', 'dovecot-lmtpd', 'dovecot-managesieved',
]

packages_bloat = ['rspamd']

clamav_packages = ['clamav', 'clamav-daemon']
clamav_daemons = ['clamav-daemon', 'clamav-freshclam']

port_info = {
    'postfix': ('smtp', 25, 'smtps', 465, 'smtp-submission', 587),
    'dovecot': ('imaps', 993, 'pop3s', 995),
}

managed_services = ['postfix', 'dovecot', 'rspamd']

managed_packages = packages + packages_bloat
app = None


class EmailServerApp(plinth.app.App):
    """FreedomBox email server app"""
    app_id = 'email_server'
    app_name = _('Email Server')

    def __init__(self):
        """The app's constructor"""
        super().__init__()
        self._add_ui_components()
        self._add_daemons()
        self._add_firewall_ports()

        # /rspamd location
        webserver = Webserver('webserver-email',  # unique id
                              'email-server-freedombox',  # config file name
                              urls=['https://{host}/rspamd'])
        self.add(webserver)

    def _add_ui_components(self):
        info = plinth.app.Info(
            app_id=self.app_id,
            version=version,
            name=self.app_name,
            short_description=_('Powered by Postfix, Dovecot & Rspamd'),
            manual_page='EmailServer',
            clients=manifest.clients,
            donation_url='https://freedomboxfoundation.org/donate/'
        )
        self.add(info)

        menu_item = plinth.menu.Menu(
            'menu_' + self.app_id,  # unique id
            info.name,  # app display name
            info.short_description,  # app description
            'roundcube',  # icon name in `static/theme/icons/`
            'email_server:index',  # view name
            parent_url_name='apps'
        )
        self.add(menu_item)

        shortcut = plinth.frontpage.Shortcut(
            'shortcut_' + self.app_id,
            name=info.name,
            short_description=info.short_description,
            icon='roundcube',
            url=reverse_lazy('email_server:my_mail'),
            clients=manifest.clients,
            login_required=True
        )
        self.add(shortcut)

    def _add_daemons(self):
        for srvname in managed_services:
            # Construct `listen_ports` parameter for the daemon
            mixed = port_info.get(srvname, ())
            port_numbers = [v for v in mixed if isinstance(v, int)]
            listen = []
            for n in port_numbers:
                listen.append((n, 'tcp4'))
                listen.append((n, 'tcp6'))
            # Add daemon
            daemon = plinth.daemon.Daemon('daemon-' + srvname, srvname,
                                          listen_ports=listen)
            self.add(daemon)

    def _add_firewall_ports(self):
        all_port_names = []
        for mixed in port_info.values():
            port_names = [v for v in mixed if isinstance(v, str)]
            all_port_names.extend(port_names)

        firewall = Firewall('firewall-email', self.app_name,
                            ports=all_port_names, is_external=True)
        self.add(firewall)

    def diagnose(self):
        """Run diagnostics and return the results"""
        results = super().diagnose()
        results.extend([r.summarize() for r in audit.domain.get()])
        results.extend([r.summarize() for r in audit.ldap.get()])
        results.extend([r.summarize() for r in audit.spam.get()])
        return results


def setup(helper, old_version=None):
    """Installs and configures module"""
    helper.install(packages)
    helper.install(packages_bloat, skip_recommends=True)
    helper.call('post', audit.ldap.repair)
    helper.call('post', audit.spam.repair)
    for srvname in managed_services:
        actions.superuser_run('service', ['reload', srvname])
    # Final step: expose service daemons to public internet
    helper.call('post', app.enable)
