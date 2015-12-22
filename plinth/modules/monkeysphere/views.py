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

from plinth import actions
from plinth import package
from plinth.modules import names

publish_process = None


@package.required(['monkeysphere'])
def index(request):
    """Serve configuration page."""
    _collect_publish_result(request)
    status = get_status()
    return TemplateResponse(
        request, 'monkeysphere.html',
        {'title': _('Monkeysphere'),
         'status': status,
         'running': bool(publish_process)})


@require_POST
def generate(request, service):
    """Generate PGP key for SSH service."""
    for domain_type in sorted(names.get_domain_types()):
        if domain_type == service:
            domain = names.get_domain(domain_type)

    try:
        actions.superuser_run(
            'monkeysphere',
            ['host-import-ssh-key', 'ssh://' + domain])
        messages.success(request, _('Generated PGP key'))
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
        messages.info(request, _('Cancelled publish key.'))

    return redirect(reverse_lazy('monkeysphere:index'))


def get_status():
    """Get the current status."""
    output = actions.superuser_run('monkeysphere', ['host-show-key'])
    keys = []
    for line in output.split('\n'):
        data = line.strip().split()
        if data and len(data) == 7:
            keys.append(dict())
            keys[-1]['pub'] = data[0]
            keys[-1]['date'] = data[1]
            keys[-1]['uid'] = data[2]
            keys[-1]['name'] = data[2].replace('ssh://', '')
            keys[-1]['pgp_fingerprint'] = data[3]
            keys[-1]['ssh_keysize'] = data[4]
            keys[-1]['ssh_fingerprint'] = data[5]
            keys[-1]['ssh_keytype'] = data[6]

    name_services = []
    for domain_type in sorted(names.get_domain_types()):
        domain = names.get_domain(domain_type)
        name_services.append({
            'type': names.get_description(domain_type),
            'short_type': domain_type,
            'name': domain or _('Not Available'),
            'available': bool(domain),
            'key': None,
        })

    # match up keys with name services
    for key in keys:
        for name_service in name_services:
            if key['name'] == name_service['name']:
                name_service['key'] = key
                continue

    return {'name_services': name_services}


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
