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
from plinth.modules import letsencrypt

logger = logging.getLogger(__name__)


def index(request):
    """Serve configuration page."""
    status = letsencrypt.get_status()
    return TemplateResponse(
        request, 'letsencrypt.html', {
            'title': letsencrypt.name,
            'description': letsencrypt.description,
            'status': status,
            'manual_page': letsencrypt.manual_page,
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
