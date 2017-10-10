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


def get_apps(request, **kwargs):
    shortcuts = frontpage.get_shortcuts()

    response = {'services': list(map(get_app_data, shortcuts)) }
    return HttpResponse(json.dumps(response, cls=DjangoJSONEncoder),
                        content_type="application/json")


def get_app_data(item):
    item_id = item['id'].split('_')[0]
    shortcut_module = module_loader.loaded_modules[item_id]

    def get_icon_url(icon):
        return 'static/theme/icons/{}.svg'.format(icon) if icon else None

    return {key: value for key, value in dict(name=shortcut_module.name,
                                              short_description=getattr(shortcut_module,
                                                                        'short_description', None),
                                              icon_url=get_icon_url(getattr(shortcut_module, 'icon', None)),
                                              description=getattr(shortcut_module, 'description', None),
                                              usage=getattr(shortcut_module, 'usage', None),
                                              manual_url=getattr(shortcut_module, 'manual_url', None),
                                              clients=getattr(shortcut_module, 'clients', None)).items() if value }


def get_access_info(request, **kwargs):
    response = {domain_type: get_domain(domain_type) for domain_type in
                get_domain_types()}
    return HttpResponse(json.dumps(response), content_type="application/json")
