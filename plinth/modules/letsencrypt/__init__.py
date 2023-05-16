# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for using Let's Encrypt."""

import json
import logging
import pathlib

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.config import DropinConfigs
from plinth.modules import names
from plinth.modules.apache.components import diagnose_url
from plinth.modules.backups.components import BackupRestore
from plinth.modules.names.components import DomainType
from plinth.package import Packages
from plinth.signals import domain_added, domain_removed, post_app_loading
from plinth.utils import format_lazy

from . import components, manifest, privileged

_description = [
    format_lazy(
        _('A digital certificate allows users of a web service to verify the '
          'identity of the service and to securely communicate with it. '
          '{box_name} can automatically obtain and setup digital '
          'certificates for each available domain.  It does so by proving '
          'itself to be the owner of a domain to Let\'s Encrypt, a '
          'certificate authority (CA).'), box_name=_(cfg.box_name)),
    _('Let\'s Encrypt is a free, automated, and open certificate '
      'authority, run for the public\'s benefit by the Internet Security '
      'Research Group (ISRG).  Please read and agree with the '
      '<a href="https://letsencrypt.org/repository/">Let\'s Encrypt '
      'Subscriber Agreement</a> before using this service.')
]

LIVE_DIRECTORY = '/etc/letsencrypt/live/'
CERTIFICATE_CHECK_DELAY = 120
logger = logging.getLogger(__name__)


class LetsEncryptApp(app_module.App):
    """FreedomBox app for Let's Encrypt."""

    app_id = 'letsencrypt'

    _version = 4

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, depends=['names'],
                               name=_('Let\'s Encrypt'), icon='fa-lock',
                               short_description=_('Certificates'),
                               description=_description,
                               manual_page='LetsEncrypt',
                               donation_url='https://letsencrypt.org/donate/')
        self.add(info)

        menu_item = menu.Menu('menu-letsencrypt', info.name,
                              info.short_description, info.icon,
                              'letsencrypt:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-letsencrypt', ['certbot'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-letsencrypt', [
            '/etc/letsencrypt/renewal-hooks/deploy/50-freedombox',
        ])
        self.add(dropin_configs)

        backup_restore = BackupRestore('backup-restore-letsencrypt',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)

        post_app_loading.connect(_certificate_handle_modified)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()

        for domain in names.components.DomainName.list():
            if domain.domain_type.can_have_certificate:
                results.append(diagnose_url('https://' + domain.name))

        if not results:
            results.append(
                (_('Cannot test: No domains are configured.'), 'warning'))

        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)


def certificate_obtain(domain):
    """Obtain a certificate for a domain and notify handlers."""
    privileged.obtain(domain)
    components.on_certificate_event('obtained', [domain], None)


def certificate_reobtain(domain):
    """Re-obtain a certificate for a domain and notify handlers.

    Don't trigger an obtained event. Re-obtaining a certificate also leads to a
    renewal (deploy) event from Let's Encrypt. Further, this event is not sent
    when obtaining the certificate for the first time. There is no easy way to
    distinguish if a renewal event is trigger because of obtain or because of
    re-obtain. Hence, handle re-obtain differently from obtain and don't
    trigger obtain event (LE will trigger a renewal event).

    """
    privileged.obtain(domain)


def certificate_revoke(domain, really_revoke=True):
    """Revoke a certificate for a domain and notify handlers.

    Revoke a certificate unless really requested to. Otherwise, simply trigger
    actions as if the certificate has been revoked. On actions such as domain
    removed, behave as if certificate has been revoked but don't actually
    revoke the certificate. Domains could be re-added later and certificates
    could be reused. Certificates are precious (due to a rate limit for
    obtaining certificates on the Let's Encrypt servers).
    """
    if really_revoke:
        privileged.revoke(domain)

    components.on_certificate_event('revoked', [domain], None)


def certificate_delete(domain):
    """Delete a certificate for a domain and notify handlers."""
    privileged.delete(domain)
    components.on_certificate_event('deleted', [domain], None)


def on_domain_added(sender, domain_type='', name='', description='',
                    services=None, **kwargs):
    """Obtain a certificate for the new domain."""
    if not DomainType.get(domain_type).can_have_certificate:
        return False

    # Check if a cert if already available
    for domain_name, domain_status in get_status()['domains'].items():
        if domain_name == name and domain_status and \
           domain_status['certificate_available'] and \
           domain_status['validity'] == 'valid':
            return False

    try:
        if name:
            logger.info('Obtaining certificate for %s', name)
            certificate_obtain(name)
        return True
    except Exception:
        return False


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Revoke Let's Encrypt certificate for the removed domain."""
    if not DomainType.get(domain_type).can_have_certificate:
        return False

    try:
        if name:
            logger.info('Revoking certificate for %s', name)
            certificate_revoke(name, really_revoke=False)
        return True
    except Exception as exception:
        logger.warning('Failed to revoke certificate for %s: %s', name,
                       exception.args[2])
        return False


def get_status():
    """Get the current settings."""
    status = privileged.get_status()

    for domain in names.components.DomainName.list():
        if domain.domain_type.can_have_certificate:
            status['domains'].setdefault(domain.name, {})

    return status


def _certificate_handle_modified(**kwargs):
    """Generate events for certificates that got modified during downtime.

    This runs as a synchronous method soon after initializing the apps. After
    this is done, remaining initialization happens.

    This method is a wrapper over the read method to catch and print
    exceptions.

    """
    logger.info('Checking if any Let\'s Encrypt certificates got renewed.')
    try:
        _certificate_handle_modified_internal()
    except Exception:
        logger.exception('Error triggering certificate events.')


def _certificate_handle_modified_internal():
    """Generate events for certificates that got modified during downtime."""
    status = get_status()
    for domain, domain_status in status['domains'].items():
        if not domain_status:
            continue

        lineage = domain_status['lineage']
        modified_time = domain_status['modified_time']
        if certificate_get_last_seen_modified_time(lineage) < modified_time:
            logger.info('Certificate for %s got renewed offline.', domain)
            components.on_certificate_event_sync('renewed', domain, lineage)
        else:
            logger.info('Certificate for %s is already the latest known.',
                        domain)


def certificate_get_last_seen_modified_time(lineage):
    """Return the last seen expiry date of a certificate."""
    from plinth import kvstore
    info = kvstore.get_default('letsencrypt_certificate_info', '{}')
    info = json.loads(info)
    try:
        return info[str(lineage)]['last_seen_modified_time']
    except KeyError:
        return 0


def certificate_set_last_seen_modified_time(lineage):
    """Write to store a certificate's last seen expiry date."""
    lineage = pathlib.Path(lineage)
    modified_time = privileged.get_modified_time(lineage.name)

    from plinth import kvstore
    info = kvstore.get_default('letsencrypt_certificate_info', '{}')
    info = json.loads(info)

    certificate_info = info.setdefault(str(lineage), {})
    certificate_info['last_seen_modified_time'] = modified_time

    kvstore.set('letsencrypt_certificate_info', json.dumps(info))
