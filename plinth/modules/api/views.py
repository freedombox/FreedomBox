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
    def get_value(key, value):
        return str(value) if key != 'icon' \
            else 'static/theme/icons/{}.svg'.format(value)

    def filter_app_data(app):
        return {key: get_value(key, value) for key, value in app.items()
                if key in ('name', 'short_description', 'icon')}

    return list(map(filter_app_data, enabled_apps))


def get_access_info(request, **kwargs):
    response = {domain_type: get_domain(domain_type) for domain_type in
                get_domain_types()}
    return HttpResponse(json.dumps(response), content_type="application/json")
