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

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg, module_loader
from plinth.errors import ActionError
from plinth.menu import main_menu
from plinth.modules import config, names
from plinth.signals import domain_added, domain_removed, domainname_change
from plinth.utils import format_lazy

from .manifest import backup

version = 2

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

service = None

manual_page = 'LetsEncrypt'

MODULES_WITH_HOOKS = ['ejabberd']
LIVE_DIRECTORY = '/etc/letsencrypt/live/'
logger = logging.getLogger(__name__)


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'fa-lock', 'letsencrypt:index',
                     short_description)
    domainname_change.connect(on_domainname_change)
    domain_added.connect(on_domain_added)
    domain_removed.connect(on_domain_removed)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    actions.superuser_run(
        'letsencrypt',
        ['setup', '--old-version', str(old_version)])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            results.append(action_utils.diagnose_url('https://' + domain))

    return results


def try_action(domain, action):
    actions.superuser_run('letsencrypt', [action, '--domain', domain])


def enable_renewal_management(domain):
    if domain == config.get_domainname():
        try:
            actions.superuser_run('letsencrypt', ['manage_hooks', 'enable'])
            logger.info(
                _('Certificate renewal management enabled for {domain}.')
                .format(domain=domain))
        except ActionError as exception:
            logger.error(
                _('Failed to enable certificate renewal management for '
                  '{domain}: {error}').format(domain=domain,
                                              error=exception.args[2]))


def on_domainname_change(sender, old_domainname, new_domainname, **kwargs):
    """Disable renewal hook management after a domain name change."""
    del sender  # Unused
    del new_domainname  # Unused
    del kwargs  # Unused

    for module in MODULES_WITH_HOOKS:
        actions.superuser_run(
            module, ['letsencrypt', 'drop', '--domain', old_domainname],
            run_in_background=True)
    actions.superuser_run(
        'letsencrypt', ['manage_hooks', 'disable', '--domain', old_domainname],
        run_in_background=True)


def get_manage_hooks_status():
    """Return status of hook management for current domain."""
    try:
        output = actions.superuser_run('letsencrypt',
                                       ['manage_hooks', 'status'])
    except ActionError:
        return False

    return output.strip()


def get_installed_modules():
    installed_modules = [
        module_name
        for module_name, module in module_loader.loaded_modules.items()
        if module_name in MODULES_WITH_HOOKS
        and module.setup_helper.get_state() == 'up-to-date'
    ]

    return installed_modules


def on_domain_added(sender, domain_type='', name='', description='',
                    services=None, **kwargs):
    """Obtain a certificate for the new domain"""
    if domain_type == 'hiddenservice':
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
            logger.info("Obtaining a Let\'s Encrypt certificate for " + name)
            try_action(name, 'obtain')
            enable_renewal_management(name)
        return True
    except ActionError as ex:
        return False


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Revoke Let's Encrypt certificate for the removed domain"""
    try:
        # Revoking certs during tests or empty names isn't expected to succeed
        if sender != 'test' and name:
            logger.info("Revoking the Let\'s Encrypt certificate for " + name)
            try_action(name, 'revoke')
        return True
    except ActionError as exception:
        logger.warn(
            ('Failed to revoke certificate for domain {domain}: {error}')
            .format(domain=name, error=exception.args[2]))
        return False


def get_status():
    """Get the current settings."""
    status = actions.superuser_run('letsencrypt', ['get-status'])
    status = json.loads(status)
    curr_dom = config.get_domainname()
    current_domain = {
        'name':
            curr_dom,
        'has_cert': (curr_dom in status['domains']
                     and status['domains'][curr_dom]['certificate_available']),
        'manage_hooks_status':
            get_manage_hooks_status()
    }
    status['current_domain'] = current_domain

    for domain_type, domains in names.domains.items():
        # XXX: Remove when Let's Encrypt supports .onion addresses
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            status['domains'].setdefault(domain, {})

    return status
