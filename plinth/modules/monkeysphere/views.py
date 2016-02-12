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
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
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
def generate(request, domain):
    """Generate PGP key for SSH service."""
    valid_domain = any((domain in domains
                        for domains in names.domains.values()))
    if valid_domain:
        try:
            actions.superuser_run(
                'monkeysphere', ['host-import-ssh-key', 'ssh://' + domain])
            messages.success(request, _('Generated PGP key.'))
        except actions.ActionError as exception:
            messages.error(request, str(exception))

    return redirect(reverse_lazy('monkeysphere:index'))


@require_POST
def publish(request, fingerprint):
    """Publish PGP key for SSH service."""
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
        publish_process.terminate()
        publish_process = None
        messages.info(request, _('Cancelled key publishing.'))

    return redirect(reverse_lazy('monkeysphere:index'))


def get_status():
    """Get the current status."""
    output = actions.superuser_run('monkeysphere', ['host-show-keys'])
    keys = {}
    for key in json.loads(output)['keys']:
        key['name'] = key['uid'].replace('ssh://', '')
        keys[key['name']] = key

    domains = []
    for domains_of_a_type in names.domains.values():
        for domain in domains_of_a_type:
            domains.append({
                'name': domain,
                'key': keys.get(domain),
            })

    return {'domains': domains}


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
