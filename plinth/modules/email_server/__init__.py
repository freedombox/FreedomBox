"""FreedomBox email server app"""
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

import plinth.app
import plinth.daemon
import plinth.frontpage
import plinth.menu
from plinth.modules.firewall.components import Firewall

from . import audit
from . import manifest

version = 1
managed_packages = ['postfix', 'dovecot-pop3d', 'dovecot-imapd',
                    'dovecot-lmtpd', 'dovecot-ldap', 'dovecot-managesieved']
managed_services = ['postfix', 'dovecot']
app = None


class EmailServerApp(plinth.app.App):
    """FreedomBox email server app"""
    app_id = 'email_server'

    def __init__(self):
        """The app's constructor"""
        super().__init__()

        info = plinth.app.Info(
            app_id=self.app_id,
            version=version,
            name=_('Email Server'),
            short_description=_('An email server for FreedomBox'),
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
            configure_url=reverse_lazy('email_server'),
            clients=manifest.clients,
            login_required=True
        )
        self.add(shortcut)

        postfix_ports = []
        dovecot_ports = []
        all_firewalld_ports = []
        for port in (25, 465, 587):
            postfix_ports.extend([(port, 'tcp4'), (port, 'tcp6')])
        for port in (993, 995):
            dovecot_ports.extend([(port, 'tcp4'), (port, 'tcp6')])
        all_firewalld_ports.extend(['smtp', 'smtps', 'smtp-submission'])
        all_firewalld_ports.extend(['pop3s', 'imaps'])

        # Manage daemons
        postfixd = plinth.daemon.Daemon('daemon-postfix', 'postfix',
                                        listen_ports=postfix_ports)
        dovecotd = plinth.daemon.Daemon('daemon-dovecot', 'dovecot',
                                        listen_ports=dovecot_ports)
        self.add(postfixd)
        self.add(dovecotd)

        # Ports
        firewall = Firewall('firewall-email', info.name,
                            ports=all_firewalld_ports, is_external=True)
        self.add(firewall)

    def diagnose(self):
        """Run diagnostics and return the results"""
        results = super().diagnose()
        results.append(audit.domain.get().summarize())
        results.append(audit.ldap.get().summarize())
        return results


def setup(helper, old_version=None):
    """Installs and configures module"""
    helper.install(managed_packages)
    helper.call('post', audit.ldap.repair)