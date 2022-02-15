# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to manage an email server.
"""

import logging

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

import plinth.app
from plinth import actions, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.config import get_domainname
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.package import Packages, remove
from plinth.signals import domain_added, domain_removed

from . import audit, manifest

clamav_packages = ['clamav', 'clamav-daemon']
clamav_daemons = ['clamav-daemon', 'clamav-freshclam']

_description = [
    _('This is a complete email server solution using Postfix, Dovecot, '
      'Rspamd and ClamAV. Postfix sends and receives emails. Dovecot allows '
      'email clients to access your mailbox using IMAP and POP3. Rspamd deals '
      'with spam. ClamAV identifies viruses and malware.'),
    _('<a href="/plinth/apps/roundcube/">Roundcube app</a> provides web '
      'interface for users to access email.'),
    _('During installation, any other email servers in the system will be '
      'uninstalled.')
]

app = None
logger = logging.getLogger(__name__)


class EmailApp(plinth.app.App):
    """FreedomBox app for an email server."""
    app_id = 'email'

    _version = 1

    def __init__(self):
        """The app's constructor"""
        super().__init__()

        info = plinth.app.Info(app_id=self.app_id, version=self._version,
                               name=_('Postfix/Dovecot'),
                               icon_filename='email',
                               short_description=_('Email Server'),
                               description=_description, manual_page='Email',
                               clients=manifest.clients,
                               donation_url='https://rspamd.com/support.html')
        self.add(info)

        menu_item = menu.Menu('menu-email', info.name, info.short_description,
                              info.icon_filename, 'email:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-email', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('email:index'), clients=info.clients,
            login_required=True)
        self.add(shortcut)

        # Other likely install conflicts have been discarded:
        # - msmtp, nullmailer, sendmail don't cause install faults.
        # - qmail and smail are missing in Bullseye (Not tested,
        #   but less likely due to that).
        packages = Packages(
            'packages-email', [
                'postfix', 'postfix-ldap', 'postfix-sqlite', 'dovecot-pop3d',
                'dovecot-imapd', 'dovecot-ldap', 'dovecot-lmtpd',
                'dovecot-managesieved', 'rspamd', 'redis-server', 'openssl'
            ], conflicts=['exim4-base', 'exim4-config', 'exim4-daemon-light'],
            conflicts_action=Packages.ConflictsAction.IGNORE)
        self.add(packages)

        listen_ports = [(25, 'tcp4'), (25, 'tcp6'), (465, 'tcp4'),
                        (465, 'tcp6'), (587, 'tcp4'), (587, 'tcp6')]
        daemon = Daemon('daemon-email-postfix', 'postfix',
                        listen_ports=listen_ports)
        self.add(daemon)

        listen_ports = [(143, 'tcp4'), (143, 'tcp6'), (993, 'tcp4'),
                        (993, 'tcp6'), (110, 'tcp4'), (110, 'tcp6'),
                        (995, 'tcp4'), (995, 'tcp6'), (4190, 'tcp4'),
                        (4190, 'tcp6')]
        daemon = Daemon('daemon-email-dovecot', 'dovecot',
                        listen_ports=listen_ports)
        self.add(daemon)

        listen_ports = [(11332, 'tcp4'), (11332, 'tcp6'), (11333, 'tcp4'),
                        (11333, 'tcp6'), (11334, 'tcp4'), (11334, 'tcp6')]
        daemon = Daemon('daemon-email-rspamd', 'rspamd',
                        listen_ports=listen_ports)
        self.add(daemon)

        daemon = Daemon('daemon-email-redis', 'redis-server',
                        listen_ports=[(6379, 'tcp4'), (6379, 'tcp6')])
        self.add(daemon)

        port_names = [
            'smtp', 'smtps', 'smtp-submission', 'imaps', 'pop3s', 'managesieve'
        ]
        firewall = Firewall('firewall-email', info.name, ports=port_names,
                            is_external=True)
        self.add(firewall)

        # /rspamd location
        webserver = Webserver(
            'webserver-email',  # unique id
            'email-freedombox',  # config file name
            urls=['https://{host}/rspamd'])
        self.add(webserver)

        # Let's Encrypt event hook
        letsencrypt = LetsEncrypt(
            'letsencrypt-email-postfix', domains='*', daemons=['postfix'],
            should_copy_certificates=True,
            private_key_path='/etc/postfix/letsencrypt/{domain}/chain.pem',
            certificate_path='/etc/postfix/letsencrypt/{domain}/chain.pem',
            user_owner='root', group_owner='root', managing_app='email')
        self.add(letsencrypt)

        letsencrypt = LetsEncrypt(
            'letsencrypt-email-dovecot', domains='*', daemons=['dovecot'],
            should_copy_certificates=True,
            private_key_path='/etc/dovecot/letsencrypt/{domain}/privkey.pem',
            certificate_path='/etc/dovecot/letsencrypt/{domain}/cert.pem',
            user_owner='root', group_owner='root', managing_app='email')
        self.add(letsencrypt)

        backup_restore = BackupRestore('backup-restore-email',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)


def get_domains():
    """Return the list of domains configured."""
    default_domain = get_domainname()
    return [default_domain] if default_domain else []


def setup(helper, old_version=None):
    """Installs and configures module"""

    def _clear_conflicts():
        component = app.get_component('packages-email')
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
    app.get_component('letsencrypt-email-postfix').setup_certificates()
    app.get_component('letsencrypt-email-dovecot').setup_certificates()
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
