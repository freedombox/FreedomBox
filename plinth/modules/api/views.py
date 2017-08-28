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

from plinth.modules.names import get_domain, get_domain_types
from plinth import frontpage
import json


def get_apps(request, **kwargs):
    shortcuts = frontpage.get_shortcuts()

    response = {'services': get_app_payload(shortcuts)}
    return HttpResponse(json.dumps(response), content_type="application/json")


def get_app_payload(enabled_apps):
    service_apps = []
    for app in enabled_apps:
        app['icon_url'] = 'static/theme/icons/' + app['icon'] + '.svg'
        app_required_fields = dict((key, app[key]) for key in ('name', 'short_description', 'icon_url'))
        apps = {key: str(value) for key, value in app_required_fields.items()}
        service_apps.append(apps)

    return service_apps


def get_access_info(request, **kwargs):
    domain_types = get_domain_types()
    response = {}
    for domain_type in domain_types:
        response[domain_type] = get_domain(domain_type)
    return HttpResponse(json.dumps(response), content_type="application/json")