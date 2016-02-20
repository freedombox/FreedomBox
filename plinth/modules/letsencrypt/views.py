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

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
import json
import logging

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import letsencrypt
from plinth.modules import names

logger = logging.getLogger(__name__)


def index(request):
    """Serve configuration page."""
    status = get_status()

    return TemplateResponse(request, 'letsencrypt.html',
                            {'title': letsencrypt.title,
                             'description': letsencrypt.description,
                             'status': status})


@require_POST
def revoke(request, domain):
    """Revoke a certficate for a given domain."""
    try:
        actions.superuser_run('letsencrypt', ['revoke', '--domain', domain])
        messages.success(
            request, _('Certificate successfully revoked for domain {domain}')
            .format(domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to revoke certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


@require_POST
def obtain(request, domain):
    """Obtain and install a certficate for a given domain."""
    try:
        actions.superuser_run('letsencrypt', ['obtain', '--domain', domain])
        messages.success(
            request, _('Certificate successfully obtained for domain {domain}')
            .format(domain=domain))
    except ActionError as exception:
        messages.error(
            request,
            _('Failed to obtain certificate for domain {domain}: {error}')
            .format(domain=domain, error=exception.args[2]))

    return redirect(reverse_lazy('letsencrypt:index'))


def get_status():
    """Get the current settings."""
    status = actions.superuser_run('letsencrypt', ['get-status'])
    status = json.loads(status)

    for domain_type, domains in names.domains.items():
        # XXX: Remove when Let's Encrypt supports .onion addresses
        if domain_type == 'hiddenservice':
            continue

        for domain in domains:
            status['domains'].setdefault(domain, {})

    return status
