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
Views for udiskie module.
"""

from plinth.modules import udiskie
from plinth.views import ServiceView


class UdiskieView(ServiceView):
    template_name = 'udiskie.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super().get_context_data(**kwargs)
        context['devices'] = udiskie.list_devices()
        return context
