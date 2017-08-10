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
                            {'title': letsencrypt.name,
                             'description': letsencrypt.description,
                             'status': status})


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
                request,
                _('Certificate renewal management enabled for {domain}.')
                .format(domain=domain))
        except ActionError as exception:
            messages.error(
                request,
                _('Failed to enable certificate renewal management for '
                  '{domain}: {error}')
                .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def toggle_hooks(request, domain):
    """Toggle pointing of certbot's hooks to Plinth, for the current domain."""
    subcommand = 'disable' if _hooks_manage_enabled() else 'enable'
    try:
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
              '{error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def delete(request, domain):
    """Delete a certificate for a given domain."""
    try:  # also delete any potential left-over renewal config backup
        actions.superuser_run('letsencrypt', ['manage_hooks', 'disable',
                                              '--domain', domain])
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to disable certificate renewal management for {domain}: '
              '{error}')
            .format(domain=domain, error=exception.args[2]))

    try:
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
        'manage_hooks_enabled': _hooks_manage_enabled()
    }
    status['current_domain'] = current_domain

    for domain_type, domains in names.domains.items():
        # XXX: Remove when Let's Encrypt supports .onion addresses
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            status['domains'].setdefault(domain, {})

    return status


def _hooks_manage_enabled():
    """Return status of hook management for current domain."""
    try:
        output = actions.superuser_run('letsencrypt',
                                       ['manage_hooks', 'status'])
    except ActionError:
        return False
    return output.strip() == 'enabled'
