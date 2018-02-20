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

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import config
from plinth.modules import letsencrypt

logger = logging.getLogger(__name__)


def index(request):
    """Serve configuration page."""
    status = letsencrypt.get_status()
    return TemplateResponse(request, 'letsencrypt.html',
                            {'title': letsencrypt.name,
                             'description': letsencrypt.description,
                             'status': status,
                             'installed_modules':
                             letsencrypt.get_installed_modules()})


@require_POST
def revoke(request, domain):
    """Revoke a certificate for a given domain."""
    try:
        letsencrypt.try_action(domain, 'revoke')
        messages.success(
            request,
            _('Certificate successfully revoked for domain {domain}.'
              'This may take a few moments to take effect.').format(
                  domain=domain))
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
        letsencrypt.try_action(domain, 'obtain')
        messages.success(
            request,
            _('Certificate successfully obtained for domain {domain}').format(
                domain=domain))
        enable_renewal_management(request, domain)
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to obtain certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))
    return redirect(reverse_lazy('letsencrypt:index'))


def enable_renewal_management(request, domain):
    if domain == config.get_domainname():
        try:
            actions.superuser_run('letsencrypt', ['manage_hooks', 'enable'])
            messages.success(
                request,
                _('Certificate renewal management enabled for {domain}.')
                .format(domain=domain))
        except ActionError as exception:
            messages.error(
                request,
                _('Failed to enable certificate renewal management for '
                  '{domain}: {error}').format(
                      domain=domain, error=exception.args[2]))


@require_POST
def toggle_hooks(request, domain):
    """Toggle pointing of certbot's hooks to FreedomBox.

    For the current domain.

    """
    manage_hooks_status = letsencrypt.get_manage_hooks_status()
    subcommand = 'disable' if 'enabled' in manage_hooks_status else 'enable'

    try:
        if subcommand == 'disable':
            enabled_modules = [module for module in
                               letsencrypt.MODULES_WITH_HOOKS
                               if module in manage_hooks_status]
            for module in enabled_modules:
                actions.superuser_run(module, ['letsencrypt', 'drop'],
                                      run_in_background=True)
        actions.superuser_run('letsencrypt', ['manage_hooks', subcommand])
        if subcommand == 'enable':
            msg = _('Certificate renewal management enabled for {domain}.')\
                  .format(domain=domain)
        else:
            msg = _('Certificate renewal management disabled for {domain}.')\
                  .format(domain=domain)
        messages.success(request, msg)
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to switch certificate renewal management for {domain}: '
              '{error}').format(domain=domain, error=exception.args[2]))

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
    """Delete a certificate for a given domain, and cleanup renewal config."""
    manage_hooks_status = letsencrypt.get_manage_hooks_status()
    enabled_modules = [module for module in letsencrypt.MODULES_WITH_HOOKS
                       if module in manage_hooks_status]

    try:
        for module in enabled_modules:
            actions.superuser_run(module, ['letsencrypt', 'drop'],
                                  run_in_background=True)
        actions.superuser_run('letsencrypt',
                              ['manage_hooks', 'disable', '--domain', domain])
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to disable certificate renewal management for {domain}: '
              '{error}').format(domain=domain, error=exception.args[2]))

    try:
        actions.superuser_run('letsencrypt', ['delete', '--domain', domain])
        messages.success(
            request,
            _('Certificate successfully deleted for domain {domain}').format(
                domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to delete certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))
