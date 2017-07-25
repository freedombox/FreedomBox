#
# This file is part of Plinth.
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
Plinth module for using Let's Encrypt.
"""

import json
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import letsencrypt
from plinth.modules import names
from plinth.modules.config import config

logger = logging.getLogger(__name__)


def index(request):
    """Serve configuration page."""
    status = get_status()
    return TemplateResponse(request, 'letsencrypt.html',
                            {'title': letsencrypt.title,
                             'description': letsencrypt.description,
                             'status': status,
                             'installed_modules':
                             letsencrypt.get_installed_modules()})


@require_POST
def revoke(request, domain):
    """Revoke a certificate for a given domain."""
    try:
        actions.superuser_run('letsencrypt', ['revoke', '--domain', domain])
        messages.success(
            request, _('Certificate successfully revoked for domain {domain}.'
                       'This may take a few moments to take effect.')
            .format(domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to revoke certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def obtain(request, domain):
    """Obtain and install a certificate for a given domain."""
    try:
        actions.superuser_run('letsencrypt', ['obtain', '--domain', domain])
        actions.superuser_run('letsencrypt', ['manage_hooks', 'enable'])
        messages.success(
            request, _('Certificate successfully obtained for domain {domain}')
            .format(domain=domain))
        successful_obtain = True
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to obtain certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))
        successful_obtain = False

    if domain == config.get_domainname() and successful_obtain:
        try:
            actions.superuser_run('letsencrypt', ['manage_hooks', 'enable'])
            messages.success(
                request, _('Certificate management enabled for {domain}.')
                .format(domain=domain))
        except ActionError as exception:
            messages.error(
                request,
                _('Failed to enable certificate management for {domain}: '
                  '{error}')
                .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def toggle_hooks(request, domain):
    """Toggle pointing of certbot's hooks to Plinth, for the current domain."""
    manage_hooks_status = letsencrypt.get_manage_hooks_status()
    subcommand = 'disable' if 'enabled' in manage_hooks_status else 'enable'

    try:
        if subcommand == 'disable':
            enabled_modules = [module for module in
                               letsencrypt.MODULES_WITH_HOOKS
                               if module in manage_hooks_status]
            for module in enabled_modules:
                actions.superuser_run(module, ['letsencrypt', 'drop'],
                                      async=True)
        actions.superuser_run('letsencrypt', ['manage_hooks', subcommand])
        messages.success(
            request, _('Certificate management changed for domain {domain}')
            .format(domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to switch certificate management for {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def toggle_module(request, domain, module):
    """Toggle usage of LE cert for a module name, for the current domain."""
    manage_hooks_status = letsencrypt.get_manage_hooks_status()
    enabled_modules = [module for module in letsencrypt.MODULES_WITH_HOOKS
                       if module in manage_hooks_status]

    if module in enabled_modules:
        mod_le_arg = 'drop'
        enabled_modules.remove(module)
    else:
        mod_le_arg = 'add'
        enabled_modules.append(module)

    module_args = ['letsencrypt', mod_le_arg]
    le_arguments = ['manage_hooks', 'enable']

    if not enabled_modules == []:
        le_arguments.extend(['--modules', ' '.join(enabled_modules)])

    try:
        actions.superuser_run(module, module_args)
        actions.superuser_run('letsencrypt', le_arguments)
        messages.success(
            request, _('Switched use of certificate for app {module}')
            .format(module=module))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to switch certificate use for app {module}: {error}')
            .format(module=module, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def delete(request, domain):
    """Delete a certificate for a given domain."""
    manage_hooks_status = letsencrypt.get_manage_hooks_status()
    enabled_modules = [module for module in letsencrypt.MODULES_WITH_HOOKS
                       if module in manage_hooks_status]

    try:
        for module in enabled_modules:
            actions.superuser_run(module, ['letsencrypt', 'drop'], async=True)
        actions.superuser_run('letsencrypt', ['delete', '--domain', domain])
        messages.success(
            request, _('Certificate successfully deleted for domain {domain}')
            .format(domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to delete certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


def get_status():
    """Get the current settings."""
    status = actions.superuser_run('letsencrypt', ['get-status'])
    status = json.loads(status)
    curr_dom = config.get_domainname()
    current_domain = {
        'name': curr_dom,
        'has_cert': (curr_dom in status['domains'] and
                     status['domains'][curr_dom]['certificate_available']),
        'manage_hooks_status': letsencrypt.get_manage_hooks_status()
    }
    status['current_domain'] = current_domain

    for domain_type, domains in names.domains.items():
        # XXX: Remove when Let's Encrypt supports .onion addresses
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            status['domains'].setdefault(domain, {})

    return status
