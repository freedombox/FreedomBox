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

        # Other likely install conflicts have been discarded:
        # - msmtp, nullmailer, sendmail don't cause install faults.
        # - qmail and smail are missing in Bullseye (Not tested,
        #   but less likely due to that).
        packages = Packages(
            'packages-email-server', [
                'postfix', 'postfix-ldap', 'postfix-sqlite', 'dovecot-pop3d',
                'dovecot-imapd', 'dovecot-ldap', 'dovecot-lmtpd',
                'dovecot-managesieved'
            ], conflicts=['exim4-base', 'exim4-config', 'exim4-daemon-light'],
            conflicts_action=Packages.ConflictsAction.IGNORE)
        self.add(packages)

        packages = Packages('packages-email-server-skip-rec', ['rspamd'],
                            skip_recommends=True)
        self.add(packages)

        listen_ports = [(25, 'tcp4'), (25, 'tcp6'), (465, 'tcp4'),
                        (465, 'tcp6'), (587, 'tcp4'), (587, 'tcp6')]
        daemon = plinth.daemon.Daemon('daemon-postfix', 'postfix',
                                      listen_ports=listen_ports)
        self.add(daemon)

        listen_ports = [(143, 'tcp4'), (143, 'tcp6'), (993, 'tcp4'),
                        (993, 'tcp6'), (110, 'tcp4'), (110, 'tcp6'),
                        (995, 'tcp4'), (995, 'tcp6'), (4190, 'tcp4'),
                        (4190, 'tcp6')]
        daemon = plinth.daemon.Daemon('daemon-dovecot', 'dovecot',
                                      listen_ports=listen_ports)
        self.add(daemon)

        listen_ports = [(11332, 'tcp4'), (11332, 'tcp6'), (11333, 'tcp4'),
                        (11333, 'tcp6'), (11334, 'tcp4'), (11334, 'tcp6')]
        daemon = plinth.daemon.Daemon('daemon-rspamd', 'rspamd',
                                      listen_ports=listen_ports)
        self.add(daemon)

        port_names = ['smtp', 'smtps', 'smtp-submission', 'imaps', 'pop3s']
        firewall = Firewall('firewall-email', info.name, ports=port_names,
                            is_external=True)
        self.add(firewall)

        # /rspamd location
        webserver = Webserver(
            'webserver-email',  # unique id
            'email-server-freedombox',  # config file name
            urls=['https://{host}/rspamd'])
        self.add(webserver)

        # Let's Encrypt event hook
        letsencrypt = LetsEncrypt(
            'letsencrypt-email-server-postfix', domains='*',
            daemons=['postfix'], should_copy_certificates=True,
            private_key_path='/etc/postfix/letsencrypt/{domain}/chain.pem',
            certificate_path='/etc/postfix/letsencrypt/{domain}/chain.pem',
            user_owner='root', group_owner='root', managing_app='email_server')
        self.add(letsencrypt)

        letsencrypt = LetsEncrypt(
            'letsencrypt-email-server-dovecot', domains='*',
            daemons=['dovecot'], should_copy_certificates=True,
            private_key_path='/etc/dovecot/letsencrypt/{domain}/privkey.pem',
            certificate_path='/etc/dovecot/letsencrypt/{domain}/cert.pem',
            user_owner='root', group_owner='root', managing_app='email_server')
        self.add(letsencrypt)

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
    app.get_component('letsencrypt-email-server-postfix').setup_certificates()
    app.get_component('letsencrypt-email-server-dovecot').setup_certificates()
    helper.call('post', audit.domain.set_domains)
    helper.call('post', audit.ldap.repair)
    helper.call('post', audit.spam.repair)

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


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Handle removal of a domain."""
    if app.needs_setup():
        return

    audit.domain.set_domains()
