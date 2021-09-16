# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for using Let's Encrypt.
"""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from plinth.errors import ActionError
from plinth.modules import letsencrypt

logger = logging.getLogger(__name__)


def index(request):
    """Serve configuration page."""
    status = letsencrypt.get_status()
    return TemplateResponse(
        request, 'letsencrypt.html', {
            'app_id': 'letsencrypt',
            'app_info': letsencrypt.app.info,
            'status': status,
            'has_diagnostics': True,
            'is_enabled': letsencrypt.app.is_enabled(),
        })


@require_POST
def revoke(request, domain):
    """Revoke a certificate for a given domain."""
    try:
        letsencrypt.certificate_revoke(domain)
        messages.success(
            request,
            _('Certificate successfully revoked for domain {domain}.'
              'This may take a few moments to take effect.').format(
                  domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to revoke certificate for domain {domain}: {error}').
            format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def obtain(request, domain):
    """Obtain and install a certificate for a given domain."""
    try:
        letsencrypt.certificate_obtain(domain)
        messages.success(
            request,
            _('Certificate successfully obtained for domain {domain}').format(
                domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to obtain certificate for domain {domain}: {error}').
            format(domain=domain, error=exception.args[2]))
    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def reobtain(request, domain):
    """Re-obtain a certificate for a given domain."""
    try:
        letsencrypt.certificate_reobtain(domain)
        messages.success(
            request,
            _('Certificate successfully obtained for domain {domain}').format(
                domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to obtain certificate for domain {domain}: {error}').
            format(domain=domain, error=exception.args[2]))
    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def delete(request, domain):
    """Delete a certificate for a given domain, and cleanup renewal config."""
    try:
        letsencrypt.certificate_delete(domain)
        messages.success(
            request,
            _('Certificate successfully deleted for domain {domain}').format(
                domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to delete certificate for domain {domain}: {error}').
            format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))
