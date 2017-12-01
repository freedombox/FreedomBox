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

from plinth.modules.names import get_domain, get_domain_types
from plinth import frontpage
from plinth import module_loader
import json


def get_access_info(request, **kwargs):
    response = {
        domain_type: get_domain(domain_type)
        for domain_type in get_domain_types()
    }
    return HttpResponse(json.dumps(response), content_type="application/json")


def get_services(request, **kwargs):
    services = [shortcut['id'].split('_')[0]
                for shortcut in frontpage.get_shortcuts()]
    response = {'services': list(map(_get_service_data, services))}
    return HttpResponse(
        json.dumps(response, cls=DjangoJSONEncoder),
        content_type="application/json")


def _get_service_data(service):
    module = module_loader.loaded_modules[service]

    def _getattr(attr, not_found=None):
        """A closure to get the enclosed module's attributes"""
        return getattr(module, attr, not_found)

    return {
        key: value
        for key, value in dict(
            name=module.name,
            short_description=_getattr('short_description'),
            icon_url=_get_icon_url(_getattr('icon')),
            description=_getattr('description'),
            usage=_getattr('usage'),
            manual_url=_getattr('manual_url'),
            clients=_getattr('clients')).items()
    }


def _get_icon_url(icon):
    return 'static/theme/icons/{}.svg'.format(icon) if icon else None
