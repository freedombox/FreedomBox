# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for api for android app.
"""

import copy
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse
from django.templatetags.static import static

from plinth import frontpage
from plinth.modules import names


def access_info(request: HttpRequest, **kwargs) -> HttpResponse:
    """API view to return a list of domains and types."""
    domains = [{
        'domain': domain.name,
        'type': domain.domain_type.component_id
    } for domain in names.components.DomainName.list()]
    response = {'domains': domains}

    return HttpResponse(json.dumps(response), content_type='application/json')


def shortcuts(request, **kwargs):
    """API view to return the list of frontpage services."""
    # XXX: Get the module (or module name) from shortcut properly.
    username = str(request.user) if request.user.is_authenticated else None
    response = get_shortcuts_as_json(username)
    return HttpResponse(json.dumps(response, cls=DjangoJSONEncoder),
                        content_type='application/json')


def get_shortcuts_as_json(username=None):
    shortcuts = [
        _get_shortcut_data(shortcut)
        for shortcut in frontpage.Shortcut.list(username)
        if shortcut.component_id and shortcut.is_enabled()
    ]
    shortcuts += frontpage.get_custom_shortcuts()['shortcuts']
    return {'shortcuts': shortcuts}


def _get_shortcut_data(shortcut):
    """Return detailed information about a shortcut."""
    shortcut_data = {
        'name': shortcut.name,
        'description': shortcut.description,
        'icon_url': _get_icon_url(shortcut.app_id, shortcut.icon),
        'clients': copy.deepcopy(shortcut.clients),
        'tags': copy.deepcopy(shortcut.tags),
    }
    # XXX: Fix the hardcoding
    if shortcut.name.startswith('shortcut-ikiwiki-'):
        shortcut_data['clients'][0]['platforms'][0]['url'] += '/{}'.format(
            shortcut['name'])
    return shortcut_data


def _get_icon_url(app_id, icon_name):
    """Return icon path given app's ID and icon name."""
    if not icon_name:
        return None

    if icon_name.startswith('/'):
        return icon_name

    if app_id:
        return static(f'{app_id}') + f'/icons/{icon_name}.png'

    return static(f'theme/icons/{icon_name}.png')
