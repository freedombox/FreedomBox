# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for using Let's Encrypt.
"""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from plinth.modules import letsencrypt
from plinth.views import AppView, messages_error

logger = logging.getLogger(__name__)


class LetsEncryptAppView(AppView):
    """Show Let's Encrypt app main page."""

    app_id = 'letsencrypt'
    template_name = 'letsencrypt.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = letsencrypt.get_status()
        return context


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
    except Exception as exception:
        messages_error(
            request,
            _('Failed to revoke certificate for domain {domain}').format(
                domain=domain), exception)

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
    except Exception as exception:
        messages_error(
            request,
            _('Failed to obtain certificate for domain {domain}').format(
                domain=domain), exception)

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
    except Exception as exception:
        messages_error(
            request,
            _('Failed to obtain certificate for domain {domain}').format(
                domain=domain), exception)

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
    except Exception as exception:
        messages_error(
            request,
            _('Failed to delete certificate for domain {domain}').format(
                domain=domain), exception)

    return redirect(reverse_lazy('letsencrypt:index'))
