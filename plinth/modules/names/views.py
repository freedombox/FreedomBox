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
Plinth module for name services
"""

from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from . import SERVICES, get_domain_types, get_description
from . import get_domain, get_services_status
from plinth.modules import names


def index(request):
    """Serve name services page."""
    status = get_status()

    return TemplateResponse(request, 'names.html',
                            {'title': names.title,
                             'status': status})


def get_status():
    """Get configured services per name."""
    name_services = []
    for domain_type in sorted(get_domain_types()):
        domain = get_domain(domain_type)
        name_services.append({
            'type': get_description(domain_type),
            'name': domain or _('Not Available'),
            'services_enabled': get_services_status(domain_type, domain),
        })

    return {
        'services': [service[1] for service in SERVICES],
        'name_services': name_services,
    }
