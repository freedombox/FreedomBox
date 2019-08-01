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
FreedomBox app for using Let's Encrypt.
"""

import json
import logging
import pathlib

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.errors import ActionError
from plinth.modules import names
from plinth.signals import (domain_added, domain_removed, domainname_change,
                            post_module_loading)
from plinth.utils import format_lazy

from . import components
from .manifest import backup  # noqa, pylint: disable=unused-import

version = 3

is_essential = True

depends = ['names']

managed_packages = ['certbot']

name = _('Let\'s Encrypt')

short_description = _('Certificates')

description = [
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

manual_page = 'LetsEncrypt'

LIVE_DIRECTORY = '/etc/letsencrypt/live/'
CERTIFICATE_CHECK_DELAY = 120
logger = logging.getLogger(__name__)

app = None


class LetsEncryptApp(app_module.App):
    """FreedomBox app for Let's Encrypt."""

    app_id = 'letsencrypt'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-letsencrypt', name, short_description,
                              'fa-lock', 'letsencrypt:index',
                              parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the module."""
    global app
    app = LetsEncryptApp()
    app.set_enabled(True)

    domainname_change.connect(on_domainname_change)
    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)

    post_module_loading.connect(_certificate_handle_modified)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    actions.superuser_run(
        'letsencrypt',
        ['setup', '--old-version', str(old_version)])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    for domain in names.components.DomainName.list():
        if domain.domain_type.can_have_certificate:
            results.append(action_utils.diagnose_url('https://' + domain.name))

    return results


def certificate_obtain(domain):
    """Obtain a certificate for a domain and notify handlers."""
    actions.superuser_run('letsencrypt', ['obtain', '--domain', domain])
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
    actions.superuser_run('letsencrypt', ['obtain', '--domain', domain])


def certificate_revoke(domain):
    """Revoke a certificate for a domain and notify handlers."""
    actions.superuser_run('letsencrypt', ['revoke', '--domain', domain])
    components.on_certificate_event('revoked', [domain], None)


def certificate_delete(domain):
    """Delete a certificate for a domain and notify handlers."""
    actions.superuser_run('letsencrypt', ['delete', '--domain', domain])
    components.on_certificate_event('deleted', [domain], None)


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Drop the certificate after a domain name change."""
    del sender  # Unused
    del new_domainname  # Unused
    del kwargs  # Unused


def on_domain_added(sender, domain_type='', name='', description='',
                    services=None, **kwargs):
    """Obtain a certificate for the new domain"""
    if domain_type == 'domain-type-tor':
        return False

    # Check if a cert if already available
    for domain_name, domain_status in get_status()['domains'].items():
        if domain_name == name and \
           domain_status.certificate_available and \
           domain_status.validity == 'valid':
            return False

    try:
        # Obtaining certs during tests or empty names isn't expected to succeed
        if sender != 'test' and name:
            logger.info('Obtaining a Let\'s Encrypt certificate for %s', name)
            certificate_obtain(name)
        return True
    except ActionError:
        return False


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Revoke Let's Encrypt certificate for the removed domain"""
    try:
        # Revoking certs during tests or empty names isn't expected to succeed
        if sender != 'test' and name:
            logger.info("Revoking the Let\'s Encrypt certificate for " + name)
            certificate_revoke(name)
        return True
    except ActionError as exception:
        logger.warning(
            ('Failed to revoke certificate for domain {domain}: {error}'
             ).format(domain=name, error=exception.args[2]))
        return False


def get_status():
    """Get the current settings."""
    status = actions.superuser_run('letsencrypt', ['get-status'])
    status = json.loads(status)

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
    output = actions.superuser_run(
        'letsencrypt', ['get-modified-time', '--domain', lineage.name])
    modified_time = int(output)

    from plinth import kvstore
    info = kvstore.get_default('letsencrypt_certificate_info', '{}')
    info = json.loads(info)

    certificate_info = info.setdefault(str(lineage), {})
    certificate_info['last_seen_modified_time'] = modified_time

    kvstore.set('letsencrypt_certificate_info', json.dumps(info))
