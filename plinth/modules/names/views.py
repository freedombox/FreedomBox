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
FreedomBox app for name services.
"""

from django.template.response import TemplateResponse

from plinth.modules import names

from . import components


def index(request):
    """Serve name services page."""
    status = get_status()

    return TemplateResponse(
        request, 'names.html', {
            'title': names.name,
            'name': names.name,
            'description': names.description,
            'manual_page': names.manual_page,
            'status': status
        })


def get_status():
    """Get configured services per name."""
    domains = components.DomainName.list()
    used_domain_types = {domain.domain_type for domain in domains}
    unused_domain_types = [
        domain_type for domain_type in components.DomainType.list().values()
        if domain_type not in used_domain_types
    ]

    return {'domains': domains, 'unused_domain_types': unused_domain_types}
