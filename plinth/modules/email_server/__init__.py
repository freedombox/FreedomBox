"""FreedomBox email server app"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import plinth.app
import plinth.daemon
import plinth.frontpage
import plinth.menu
from plinth import actions
from plinth.modules.apache.components import Webserver
from plinth.modules.config import get_domainname
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.package import packages_installed, remove

from . import audit, manifest

version = 1

# Other likely install conflicts have been discarded:
# - msmtp, nullmailer, sendmail don't cause install faults.
# - qmail and smail are missing in Bullseye (Not tested,
#   but less likely due to that).
package_conflicts = ('exim4-base', 'exim4-config', 'exim4-daemon-light')
package_conflicts_action = 'ignore'

packages = [
    'postfix-ldap',
    'postfix-sqlite',
    'dovecot-pop3d',
    'dovecot-imapd',
    'dovecot-ldap',
    'dovecot-lmtpd',
    'dovecot-managesieved',
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

_description = [
    _('<a href="/plinth/apps/roundcube/">Roundcube app</a> provides web '
      'interface for users to access email.'),
    _('During installation, any other email servers in the system will be '
      'uninstalled.')
]

app = None
logger = logging.getLogger(__name__)


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
        webserver = Webserver(
            'webserver-email',  # unique id
            'email-server-freedombox',  # config file name
            urls=['https://{host}/rspamd'])
        self.add(webserver)

        # Let's Encrypt event hook
        default_domain = get_domainname()
        domains = [default_domain] if default_domain else []
        letsencrypt = LetsEncrypt('letsencrypt-email-server', domains=domains,
                                  daemons=['postfix', 'dovecot'],
                                  should_copy_certificates=False,
                                  managing_app='email_server')
        self.add(letsencrypt)

        if not domains:
            logger.warning('Could not fetch the FreedomBox domain name!')

    def _add_ui_components(self):
        info = plinth.app.Info(
            app_id=self.app_id, version=version, name=self.app_name,
            short_description=_('Powered by Postfix, Dovecot & Rspamd'),
            description=_description, manual_page='EmailServer',
            clients=manifest.clients,
            donation_url='https://freedomboxfoundation.org/donate/')
        self.add(info)

        menu_item = plinth.menu.Menu(
            'menu_' + self.app_id,  # unique id
            info.name,  # app display name
            info.short_description,  # app description
            'roundcube',  # icon name in `static/theme/icons/`
            'email_server:index',  # view name
            parent_url_name='apps')
        self.add(menu_item)

        shortcut = plinth.frontpage.Shortcut(
            'shortcut_' + self.app_id, name=info.name,
            short_description=info.short_description, icon='roundcube',
            url=reverse_lazy('email_server:my_mail'), clients=manifest.clients,
            login_required=True)
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
        results.extend([r.summarize() for r in audit.tls.get()])
        results.extend([r.summarize() for r in audit.rcube.get()])
        return results


def setup(helper, old_version=None):
    """Installs and configures module"""

    def _clear_conflicts():
        packages_to_remove = packages_installed(package_conflicts)
        if packages_to_remove:
            logger.info('Removing conflicting packages: %s',
                        packages_to_remove)
            remove(packages_to_remove)

    # Install
    helper.call('pre', _clear_conflicts)
    helper.install(packages)
    helper.install(packages_bloat, skip_recommends=True)

    # Setup
    helper.call('post', audit.domain.repair)
    helper.call('post', audit.ldap.repair)
    helper.call('post', audit.spam.repair)
    helper.call('post', audit.tls.repair)
    helper.call('post', audit.rcube.repair)

    # Reload
    for srvname in managed_services:
        actions.superuser_run('service', ['reload', srvname])

    # Expose to public internet
    helper.call('post', app.enable)
