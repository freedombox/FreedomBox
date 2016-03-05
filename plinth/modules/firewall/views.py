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
Plinth module to configure a firewall
"""

from django.template.response import TemplateResponse

from plinth.modules import firewall
import plinth.service as service_module


def index(request):
    """Serve introduction page"""
    if not firewall.get_enabled_status():
        return TemplateResponse(request, 'firewall.html',
                                {'title': firewall.title,
                                 'description': firewall.description,
                                 'firewall_status': 'not_running'})

    internal_enabled_services = firewall.get_enabled_services(zone='internal')
    external_enabled_services = firewall.get_enabled_services(zone='external')

    return TemplateResponse(
        request, 'firewall.html',
        {'title': firewall.title,
         'description': firewall.description,
         'services': list(service_module.services.values()),
         'internal_enabled_services': internal_enabled_services,
         'external_enabled_services': external_enabled_services})
