# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure name services.
"""

import logging
import socket
import subprocess

from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import cfg, menu, network
from plinth.daemon import Daemon
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.signals import (domain_added, domain_removed, post_hostname_change,
                            pre_hostname_change)
from plinth.utils import format_lazy

from . import components, manifest, privileged

logger = logging.getLogger(__name__)

_description = [
    format_lazy(
        _('Name Services provides an overview of the ways {box_name} can be '
          'reached from the public Internet: domain name, Tor onion service, '
          'and Pagekite. For each type of name, it is shown whether the HTTP, '
          'HTTPS, and SSH services are enabled or disabled for incoming '
          'connections through the given name.'), box_name=(cfg.box_name))
]


class NamesApp(app_module.App):
    """FreedomBox app for names."""

    app_id = 'names'

    _version = 2

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Name Services'),
                               icon='fa-tags', description=_description,
                               manual_page='NameServices')
        self.add(info)

        menu_item = menu.Menu('menu-names', info.name, None, info.icon,
                              'names:index',
                              parent_url_name='system:visibility', order=10)
        self.add(menu_item)

        # 'ip' utility is needed from 'iproute2' package.
        packages = Packages('packages-names',
                            ['systemd-resolved', 'libnss-resolve', 'iproute2'])
        self.add(packages)

        daemon = Daemon('daemon-names', 'systemd-resolved')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-names',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(diagnose_resolution('deb.debian.org'))
        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        # Fresh install or upgrading to version 2
        if old_version < 2:
            privileged.set_resolved_configuration(dns_fallback=True)

        # Load the configuration files for systemd-resolved provided by
        # FreedomBox.
        service_privileged.restart('systemd-resolved')

        # After systemd-resolved is freshly installed, /etc/resolve.conf
        # becomes a symlink to configuration pointing to systemd-resovled stub
        # resolver. However, the old contents are not fed from network-manager
        # (if it was present earlier and wrote to /etc/resolve.conf). Ask
        # network-manager to feed the DNS servers from the connections it has
        # established to systemd-resolved so that using fallback DNS servers is
        # not necessary.
        network.refeed_dns()

        self.enable()


def diagnose_resolution(domain: str) -> DiagnosticCheck:
    """Perform a diagnostic check for whether a domain can be resolved."""
    result = Result.NOT_DONE
    try:
        subprocess.run(['resolvectl', 'query', '--cache=no', domain],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=True)
        result = Result.PASSED
    except subprocess.CalledProcessError:
        result = Result.FAILED

    description = gettext_noop('Resolve domain name: {domain}')
    parameters: DiagnosticCheckParameters = {'domain': domain}
    return DiagnosticCheck('names-resolve', description, result, parameters)


def on_domain_added(sender, domain_type, name='', description='',
                    services=None, **kwargs):
    """Add domain to global list."""
    if not domain_type:
        return

    if not name:
        return
    if not services:
        services = []

    components.DomainName('domain-' + sender + '-' + name, name, domain_type,
                          services)
    logger.info('Added domain %s of type %s with services %s', name,
                domain_type, str(services))


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    if name:
        component_id = 'domain-' + sender + '-' + name
        components.DomainName.get(component_id).remove()
        logger.info('Removed domain %s of type %s', name, domain_type)
    else:
        for domain_name in components.DomainName.list():
            if domain_name.domain_type.component_id == domain_type:
                domain_name.remove()

                logger.info('Remove domain %s of type %s', domain_name.name,
                            domain_type)


######################################################
# Domain utilities meant to be used by other modules #
######################################################


def get_hostname():
    """Return the hostname."""
    return socket.gethostname()


def set_hostname(hostname):
    """Set machine hostname and send signals before and after."""
    from plinth.modules import config
    from plinth.modules.config import privileged as config_privileged

    old_hostname = get_hostname()
    domainname = config.get_domainname()

    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert
    hostname = str(hostname)

    pre_hostname_change.send_robust(sender='names', old_hostname=old_hostname,
                                    new_hostname=hostname)

    logger.info('Changing hostname to - %s', hostname)
    privileged.set_hostname(hostname)

    logger.info('Setting domain name after hostname change - %s', domainname)
    config_privileged.set_domainname(domainname)

    post_hostname_change.send_robust(sender='names', old_hostname=old_hostname,
                                     new_hostname=hostname)


def get_available_tls_domains():
    """Return an iterator with all domains able to have a certificate."""
    return (domain.name for domain in components.DomainName.list()
            if domain.domain_type.can_have_certificate)
