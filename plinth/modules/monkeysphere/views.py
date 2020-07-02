# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the monkeysphere module.
"""

import json

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions
from plinth.modules import monkeysphere, names

publish_process = None


def index(request):
    """Serve configuration page."""
    _collect_publish_result(request)
    status = get_status()
    return TemplateResponse(
        request, 'monkeysphere.html', {
            'app_info': monkeysphere.app.info,
            'title': monkeysphere.app.info.name,
            'status': status,
            'running': bool(publish_process),
            'refresh_page_sec': 3 if bool(publish_process) else None,
        })


@require_POST
def import_key(request, ssh_fingerprint):
    """Import a key into monkeysphere."""
    keys = get_keys()
    available_domains = keys[ssh_fingerprint]['available_domains']
    try:
        actions.superuser_run('monkeysphere',
                              ['host-import-key', ssh_fingerprint] +
                              list(available_domains))
        messages.success(request, _('Imported key.'))
    except actions.ActionError as exception:
        messages.error(request, str(exception))

    return redirect(reverse_lazy('monkeysphere:index'))


def details(request, fingerprint):
    """Get details for an OpenPGP key."""
    return TemplateResponse(request, 'monkeysphere_details.html', {
        'title': monkeysphere.app.info.name,
        'key': get_key(fingerprint)
    })


@require_POST
def publish(request, fingerprint):
    """Publish OpenPGP key for SSH service."""
    global publish_process
    if not publish_process:
        publish_process = actions.superuser_run(
            'monkeysphere', ['host-publish-key', fingerprint],
            run_in_background=True)

    return redirect(reverse_lazy('monkeysphere:index'))


@require_POST
def cancel(request):
    """Cancel ongoing process."""
    global publish_process
    if publish_process:
        actions.superuser_run(
            'monkeysphere', ['host-cancel-publish',
                             str(publish_process.pid)])
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

    domains = names.components.DomainName.list_names()
    for key in keys.values():
        key['imported_domains'] = set(key.get('imported_domains', []))
        key['available_domains'] = set(key.get('available_domains', []))
        if '*' in key['available_domains']:
            key['available_domains'] = set(domains)

        key['all_domains'] = sorted(key['available_domains'].union(
            key['imported_domains']))
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
