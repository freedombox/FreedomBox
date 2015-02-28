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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from gettext import gettext as _
import NetworkManager
import urllib

from plinth import cfg


CONNECTION_TYPE_NAMES = {
    '802-3-ethernet': 'Ethernet',
    '802-11-wireless': 'Wi-Fi',
    'bridge': 'Bridge',
    'bond': 'Bond',
    'gsm': 'Mobile Broadband',
    'infiniband': 'InfiniBand',
    'pppoe': 'DSL',
    'vlan': 'VLAN',
    'vpn': 'VPN',
    'wimax': 'WiMAX',
}


def init():
    """Initialize the Network module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Network'), 'glyphicon-signal', 'network:index', 18)


@login_required
def index(request):
    """Show connection list."""
    connections = []
    for conn in NetworkManager.Settings.ListConnections():
        settings = conn.GetSettings()['connection']
        # Display a friendly type name if known.
        conn_type = CONNECTION_TYPE_NAMES.get(settings['type'],
                                              settings['type'])
        connections.append({
            'name': settings['id'],
            'id': urllib.parse.quote_plus(settings['id']),
            'type': conn_type
        })
    return TemplateResponse(request, 'connections_list.html',
                            {'title': _('Network Connections'),
                             'connections': connections})


@login_required
def delete(request, conn_id):
    """Handle deleting connections, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the connection.
    """
    name = urllib.parse.unquote_plus(conn_id)
    if request.method == 'POST':
        for conn in NetworkManager.Settings.ListConnections():
            settings = conn.GetSettings()['connection']
            if settings['id'] == name:
                conn.Delete()
                messages.success(request, _('Connection %s deleted.') % name)
                return redirect(reverse_lazy('network:index'))
        messages.failure(
            request,
            _('Failed to delete connection %s: not found.') % name)
        return redirect(reverse_lazy('network:index'))

    return TemplateResponse(request, 'connections_delete.html',
                            {'title': _('Delete Connection'),
                             'name': name})
