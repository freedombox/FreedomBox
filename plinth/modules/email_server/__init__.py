"""FreedomBox email server app"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

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
from plinth.package import Packages, remove
from plinth.signals import domain_added, domain_removed

from . import audit, manifest

clamav_packages = ['clamav', 'clamav-daemon']
clamav_daemons = ['clamav-daemon', 'clamav-freshclam']

port_info = {
    'postfix': ('smtp', 25, 'smtps', 465, 'smtp-submission', 587),
    'dovecot': ('imaps', 993, 'pop3s', 995),
}

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

    _version = 1

    def __init__(self):
        """The app's constructor"""
        super().__init__()
        self._add_ui_components()

        # Other likely install conflicts have been discarded:
        # - msmtp, nullmailer, sendmail don't cause install faults.
        # - qmail and smail are missing in Bullseye (Not tested,
        #   but less likely due to that).
        packages = Packages(
            'packages-email-server', [
                'postfix-ldap', 'postfix-sqlite', 'dovecot-pop3d',
                'dovecot-imapd', 'dovecot-ldap', 'dovecot-lmtpd',
                'dovecot-managesieved'
            ], conflicts=['exim4-base', 'exim4-config', 'exim4-daemon-light'],
            conflicts_action=Packages.ConflictsAction.IGNORE)
        self.add(packages)

        packages = Packages('packages-email-server-skip-rec', ['rspamd'],
                            skip_recommends=True)
        self.add(packages)

        self._add_daemons()
        self._add_firewall_ports()

        # /rspamd location
        webserver = Webserver(
            'webserver-email',  # unique id
            'email-server-freedombox',  # config file name
            urls=['https://{host}/rspamd'])
        self.add(webserver)

        # Let's Encrypt event hook
        letsencrypt = LetsEncrypt('letsencrypt-email-server',
                                  domains=get_domains,
                                  daemons=['postfix', 'dovecot'],
                                  should_copy_certificates=False,
                                  managing_app='email_server')
        self.add(letsencrypt)

    def _add_ui_components(self):
        info = plinth.app.Info(
            app_id=self.app_id, version=self._version, name=self.app_name,
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

    def _add_daemons(self):
        for srvname in ['postfix', 'dovecot', 'rspamd']:
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

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)

    def diagnose(self):
        """Run diagnostics and return the results"""
        results = super().diagnose()
        results.extend([r.summarize() for r in audit.ldap.get()])
        results.extend([r.summarize() for r in audit.spam.get()])
        results.extend([r.summarize() for r in audit.tls.get()])
        results.extend([r.summarize() for r in audit.rcube.get()])
        return results


def get_domains():
    """Return the list of domains configured."""
    default_domain = get_domainname()
    return [default_domain] if default_domain else []


def setup(helper, old_version=None):
    """Installs and configures module"""

    def _clear_conflicts():
        component = app.get_component('packages-email-server')
        packages_to_remove = component.find_conflicts()
        if packages_to_remove:
            logger.info('Removing conflicting packages: %s',
                        packages_to_remove)
            remove(packages_to_remove)

    # Install
    helper.call('pre', _clear_conflicts)
    app.setup(old_version)

    # Setup
    helper.call('post', audit.home.repair)
    helper.call('post', audit.domain.set_domains)
    helper.call('post', audit.ldap.repair)
    helper.call('post', audit.spam.repair)
    helper.call('post', audit.tls.repair)
    helper.call('post', audit.rcube.repair)

    # Reload
    actions.superuser_run('service', ['reload', 'postfix'])
    actions.superuser_run('service', ['reload', 'dovecot'])
    actions.superuser_run('service', ['reload', 'rspamd'])

    # Expose to public internet
    helper.call('post', app.enable)


def on_domain_added(sender, domain_type, name, description='', services=None,
                    **kwargs):
    """Handle addition of a new domain."""
    if app.needs_setup():
        return

    audit.domain.set_domains()


def on_domain_removed(sender, domain_type, name, **kwargs):
    """Handle removal of a domain."""
    if app.needs_setup():
        return

    audit.domain.set_domains()
