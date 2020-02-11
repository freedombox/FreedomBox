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

from plinth import views
from plinth.modules import firewall

from . import components


class FirewallAppView(views.AppView):
    """Serve firewall index page."""
    app_id = 'firewall'
    template_name = 'firewall.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for the template."""
        context = super().get_context_data(*args, **kwargs)

        status = 'running' if firewall.get_enabled_status() else 'not_running'
        context['firewall_status'] = status

        if status == 'running':
            context['components'] = components.Firewall.list()
            internal_enabled_ports = firewall.get_enabled_services(
                zone='internal')
            external_enabled_ports = firewall.get_enabled_services(
                zone='external')
            context['internal_enabled_ports'] = internal_enabled_ports
            context['external_enabled_ports'] = external_enabled_ports

        return context
