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
FreedomBox app for api for android app.
"""

import copy
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.templatetags.static import static

from plinth import frontpage
from plinth.modules import names


def access_info(request, **kwargs):
    """API view to return a list of domains and types."""
    domains = [{
        'domain': domain,
        'type': domain_type
    } for domain_type, domains in names.domains.items() for domain in domains]
    response = {'domains': domains}

    return HttpResponse(json.dumps(response), content_type='application/json')


def shortcuts(request, **kwargs):
    """API view to return the list of frontpage services."""
    # XXX: Get the module (or module name) from shortcut properly.
    username = str(request.user) if request.user.is_authenticated else None
    response = get_shortcuts_as_json(username)
    return HttpResponse(
        json.dumps(response, cls=DjangoJSONEncoder),
        content_type='application/json')


def get_shortcuts_as_json(username=None):
    shortcuts = [
        _get_shortcut_data(shortcut)
        for shortcut in frontpage.Shortcut.list(username)
        if shortcut.component_id
    ]
    custom_shortcuts = frontpage.get_custom_shortcuts()
    if custom_shortcuts:
        shortcuts += custom_shortcuts['shortcuts']
    return {'shortcuts': shortcuts}


def _get_shortcut_data(shortcut):
    """Return detailed information about a shortcut."""
    shortcut_data = {
        'name': shortcut.name,
        'short_description': shortcut.short_description,
        'description': shortcut.description,
        'icon_url': _get_icon_url(shortcut.icon),
        'clients': copy.deepcopy(shortcut.clients),
    }
    # XXX: Fix the hardcoding
    if shortcut.name.startswith('shortcut-ikiwiki-'):
        shortcut_data['clients'][0]['platforms'][0]['url'] += '/{}'.format(
            shortcut['name'])
    return shortcut_data


def _get_icon_url(icon_name):
    """Return icon path given icon name."""
    if not icon_name:
        return None

    return static('theme/icons/{}.png'.format(icon_name))
