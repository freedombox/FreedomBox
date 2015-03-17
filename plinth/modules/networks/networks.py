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

from dbus.exceptions import DBusException
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from gettext import gettext as _
import urllib

from .forms import ConnectionTypeSelectForm, AddEthernetForm, AddWifiForm
from plinth import cfg
from plinth import network


subsubmenu = [{'url': reverse_lazy('networks:index'),
               'text': _('Network Connections')},
              {'url': reverse_lazy('networks:scan'),
               'text': _('Nearby Wi-Fi Networks')},
              {'url': reverse_lazy('networks:add'),
               'text': _('Add Connection')}]


def init():
    """Initialize the Networks module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Networks'), 'glyphicon-signal', 'networks:index', 18)


@login_required
def index(request):
    """Show connection list."""
    connections = network.get_connection_list()

    return TemplateResponse(request, 'connections_list.html',
                            {'title': _('Network Connections'),
                             'subsubmenu': subsubmenu,
                             'connections': connections})


@login_required
def edit(request, conn_id):
    """Serve connection editing form."""
    form = None
    name = urllib.parse.unquote_plus(conn_id)
    form_data = {'name': name}

    conn = network.get_connection(name)
    if not conn:
        messages.error(
            request,
            _('Cannot edit connection: %s not found.') % name)
        return redirect(reverse_lazy('networks:index'))
    settings = conn.GetSettings()

    if request.method == 'POST':
        if settings['connection']['type'] == '802-11-wireless':
            form = AddWifiForm(request.POST)
        else:
            form = AddEthernetForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            if settings['connection']['type'] == '802-3-ethernet':
                network.edit_ethernet_connection(conn, name, ipv4_method, ipv4_address)
            elif settings['connection']['type'] == '802-11-wireless':
                ssid = form.cleaned_data['ssid']
                network.edit_wifi_connection(conn, name, ssid, ipv4_method, ipv4_address)
            else:
                messages.error(
                    request,
                    _('Cannot edit connection %s: '
                      'Connection type not supported.') % name)
            return redirect(reverse_lazy('networks:index'))
    else:
        form_data['ipv4_method'] = settings['ipv4']['method']

        if settings['ipv4']['addresses']:
            form_data['ipv4_address'] = settings['ipv4']['addresses'][0][0]

        if settings['connection']['type'] == '802-11-wireless':
            form_data['ssid'] = settings['802-11-wireless']['ssid']
            form = AddWifiForm(form_data)
        else:
            form = AddEthernetForm(form_data)

        return TemplateResponse(request, 'connections_edit.html',
                                {'title': _('Edit Connection'),
                                 'subsubmenu': subsubmenu,
                                 'form': form})


@login_required
def activate(request, conn_id):
    """Activate the connection."""
    name = urllib.parse.unquote_plus(conn_id)

    try:
        network.activate_connection(name)
    except network.ConnectionNotFound as cnf:
        messages.error(request, cnf)
        return redirect(reverse_lazy('networks:index'))
    except network.DeviceNotFound as dnf:
        messages.error(request, dnf)
        return redirect(reverse_lazy('networks:index'))

    messages.success(request, _('Activated connection %s.') % name)
    return redirect(reverse_lazy('networks:index'))


@login_required
def deactivate(request, conn_id):
    """Deactivate the connection."""
    name = urllib.parse.unquote_plus(conn_id)
    try:
        network.deactivate_connection(name)
        messages.success(request, _('Deactivated connection %s.') % name)
    except network.ConnectionNotFound as cnf:
        messages.error(request, cnf)
    return redirect(reverse_lazy('networks:index'))


@login_required
def scan(request):
    """Show a list of nearby visible wifi APs."""
    aps = network.wifi_scan()
    return TemplateResponse(request, 'wifi_scan.html',
                            {'title': _('Nearby Wi-Fi Networks'),
                             'subsubmenu': subsubmenu,
                             'aps': aps})


@login_required
def connect(request, connect_path):
    """Create a new wifi connection to an existing AP."""
    form = None
    ssid = urllib.parse.unquote_plus(connect_path)
    form_data = {'name': ssid, 'ssid': ssid, 'ipv4_method': 'auto'}

    if request.method == 'POST':
        form = AddWifiForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            ssid = form.cleaned_data['ssid']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            network.add_wifi_connection(name, ssid, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('networks:index'))
    else:
        form = AddWifiForm(form_data)

        return TemplateResponse(request, 'connections_create.html',
                                {'title': _('Connect to Wi-Fi Network'),
                                 'subsubmenu': subsubmenu,
                                 'form': form})


@login_required
def add(request):
    """Serve the connection type selection form."""
    form = None

    if request.method == 'POST':
        form = ConnectionTypeSelectForm(request.POST)
        if form.is_valid():
            conn_type = form.cleaned_data['conn_type']
            if conn_type == '802-3-ethernet':
                return redirect(reverse_lazy('networks:add_ethernet'))
            elif conn_type == '802-11-wireless':
                return redirect(reverse_lazy('networks:add_wifi'))
    else:
        form = ConnectionTypeSelectForm()
        return TemplateResponse(request, 'connections_type_select.html',
                                {'title': _('Add Connection'),
                                 'subsubmenu': subsubmenu,
                                 'form': form})


@login_required
def add_ethernet(request):
    """Serve ethernet connection create form."""
    form = None

    if request.method == 'POST':
        form = AddEthernetForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            network.add_ethernet_connection(name, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('networks:index'))
    else:
        form = AddEthernetForm()

    return TemplateResponse(request, 'connections_create.html',
                            {'title': _('Editing New Ethernet Connection'),
                             'subsubmenu': subsubmenu,
                             'form': form})


@login_required
def add_wifi(request):
    """Serve wifi connection create form."""
    form = None

    if request.method == 'POST':
        form = AddWifiForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            ssid = form.cleaned_data['ssid']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            network.add_wifi_connection(name, ssid, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('networks:index'))
    else:
        form = AddWifiForm()

    return TemplateResponse(request, 'connections_create.html',
                            {'title': _('Editing New Wi-Fi Connection'),
                             'subsubmenu': subsubmenu,
                             'form': form})


@login_required
def delete(request, conn_id):
    """Handle deleting connections, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the connection.
    """
    name = urllib.parse.unquote_plus(conn_id)
    if request.method == 'POST':
        try:
            network.delete_connection(name)
        except network.ConnectionNotFound as cnf:
            messages.error(request, cnf)
        else:
            messages.success(request, _('Connection %s deleted.') % name)
        return redirect(reverse_lazy('networks:index'))

    return TemplateResponse(request, 'connections_delete.html',
                            {'title': _('Delete Connection'),
                             'subsubmenu': subsubmenu,
                             'name': name})
