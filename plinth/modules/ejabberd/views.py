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
Views for the Ejabberd module
"""

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from stronghold.decorators import public

from plinth.modules import ejabberd
from plinth.views import ServiceView


class EjabberdServiceView(ServiceView):
    """Show ejabberd as a service."""
    service_id = ejabberd.managed_services[0]
    template_name = 'ejabberd.html'
    description = ejabberd.description
    diagnostics_module_name = 'ejabberd'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['domainname'] = ejabberd.get_domainname()
        return context
