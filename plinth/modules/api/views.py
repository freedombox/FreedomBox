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
Plinth module for api for android app.
"""

from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static

from plinth import frontpage
from plinth import module_loader
from plinth.modules import names
import json


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
    shortcuts = [
        _get_shortcut_data(shortcut['id'].split('_')[0], shortcut)
        for shortcut in frontpage.get_shortcuts()
    ]
    response = {'shortcuts': shortcuts}
    return HttpResponse(
        json.dumps(response, cls=DjangoJSONEncoder),
        content_type='application/json')


def _get_shortcut_data(module_name, shortcut):
    """Return detailed information about a shortcut."""
    module = module_loader.loaded_modules[module_name]
    return {
        'name': shortcut['name'],
        'short_description': shortcut['short_description'],
        'description': shortcut['details'],
        'icon_url': _get_icon_url(shortcut['icon']),
        'clients': getattr(module, 'clients', None)
    }


def _get_icon_url(icon_name):
    """Return icon path given icon name."""
    if not icon_name:
        return None

    return static('static/theme/icons/{}.png'.format(icon_name))
