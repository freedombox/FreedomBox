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
Views for the monkeysphere module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
import json

from plinth import actions
from plinth.modules import monkeysphere
from plinth.modules import names

publish_process = None


def index(request):
    """Serve configuration page."""
    _collect_publish_result(request)
    status = get_status()
    return TemplateResponse(
        request, 'monkeysphere.html',
        {'title': monkeysphere.title,
         'description': monkeysphere.description,
         'status': status,
         'running': bool(publish_process)})


@require_POST
def import_key(request, ssh_fingerprint):
    """Import a key into monkeysphere."""
    available_domains = [domain
                         for domains in names.domains.values()
                         for domain in domains]
    try:
        actions.superuser_run(
            'monkeysphere', ['host-import-key', ssh_fingerprint] +
            available_domains)
        messages.success(request, _('Imported key.'))
    except actions.ActionError as exception:
        messages.error(request, str(exception))

    return redirect(reverse_lazy('monkeysphere:index'))


def details(request, fingerprint):
    """Get details for an OpenPGP key."""
    return TemplateResponse(request, 'monkeysphere_details.html',
                            {'title': monkeysphere.title,
                             'key': get_key(fingerprint)})


@require_POST
def publish(request, fingerprint):
    """Publish OpenPGP key for SSH service."""
    global publish_process
    if not publish_process:
        publish_process = actions.superuser_run(
            'monkeysphere', ['host-publish-key', fingerprint], async=True)

    return redirect(reverse_lazy('monkeysphere:index'))


@require_POST
def cancel(request):
    """Cancel ongoing process."""
    global publish_process
    if publish_process:
        actions.superuser_run(
            'monkeysphere', ['host-cancel-publish', str(publish_process.pid)])
        publish_process = None
        messages.info(request, _('Cancelled key publishing.'))

    return redirect(reverse_lazy('monkeysphere:index'))


def get_status():
    """Get the current status."""
    return {'keys': get_keys()}


def get_keys(fingerprint=None):
    """Get keys."""
    fingerprint = [fingerprint] if fingerprint else []
    output = actions.superuser_run('monkeysphere',
                                   ['host-show-keys'] + fingerprint)
    keys = json.loads(output)['keys']

    domains = [domain
               for domains_of_a_type in names.domains.values()
               for domain in domains_of_a_type]
    for key in keys.values():
        key['imported_domains'] = set(key.get('imported_domains', []))
        key['available_domains'] = set(key.get('available_domains', []))
        if '*' in key['available_domains']:
            key['available_domains'] = set(domains)

        key['all_domains'] = sorted(
            key['available_domains'].union(key['imported_domains']))
        key['importable_domains'] = key['available_domains'] \
            .difference(key['imported_domains'])

    return keys


def get_key(fingerprint):
    """Get key by fingerprint."""
    keys = get_keys(fingerprint)
    return list(keys.values())[0] if len(keys) else None


def _collect_publish_result(request):
    """Handle publish process completion."""
    global publish_process
    if not publish_process:
        return

    return_code = publish_process.poll()

    # Publish process is not complete yet
    if return_code is None:
        return

    if not return_code:
        messages.success(request, _('Published key to keyserver.'))
    else:
        messages.error(request, _('Error occurred while publishing key.'))

    publish_process = None
