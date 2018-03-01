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
FreedomBox app to configure a firewall.
"""

from django.template.response import TemplateResponse

import plinth.service as service_module
from plinth.modules import firewall


def index(request):
    """Serve introduction page"""
    if not firewall.get_enabled_status():
        return TemplateResponse(
            request, 'firewall.html', {
                'title': firewall.name,
                'description': firewall.description,
                'firewall_status': 'not_running'
            })

    internal_enabled_services = firewall.get_enabled_services(zone='internal')
    external_enabled_services = firewall.get_enabled_services(zone='external')

    return TemplateResponse(
        request, 'firewall.html', {
            'title': firewall.name,
            'description': firewall.description,
            'services': list(service_module.services.values()),
            'manual_page': firewall.manual_page,
            'internal_enabled_services': internal_enabled_services,
            'external_enabled_services': external_enabled_services
        })
