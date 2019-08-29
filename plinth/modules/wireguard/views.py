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
Views for WireGuard application.
"""

import plinth.modules.wireguard as wireguard
from plinth.views import AppView


class WireguardView(AppView):
    """Serve configuration page."""
    app_id = 'wireguard'
    clients = wireguard.clients
    name = wireguard.name
    description = wireguard.description
    diagnostics_module_name = 'wireguard'
    show_status_block = False
    template_name = 'wireguard.html'
    port_forwarding_info = wireguard.port_forwarding_info
