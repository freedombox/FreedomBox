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
import NetworkManager
import uuid
import urllib

from .forms import CONNECTION_TYPE_NAMES, ConnectionTypeSelectForm, \
    AddEthernetForm, AddWifiForm
from plinth import cfg


subsubmenu = [{'url': reverse_lazy('network:index'),
               'text': _('Network Connections')},
              {'url': reverse_lazy('network:add'),
               'text': _('Add Connection')}]


def init():
    """Initialize the Network module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Network'), 'glyphicon-signal', 'network:index', 18)


@login_required
def index(request):
    """Show connection list."""
    connections = get_connection_list()

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

    conn = get_connection(name)
    if not conn:
        messages.error(
            request,
            _('Cannot edit connection: %s not found.') % name)
        return redirect(reverse_lazy('network:index'))
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
                _edit_ethernet_connection(conn, name, ipv4_method, ipv4_address)
            elif settings['connection']['type'] == '802-11-wireless':
                ssid = form.cleaned_data['ssid']
                _edit_wifi_connection(conn, name, ssid, ipv4_method, ipv4_address)
            else:
                messages.error(
                    request,
                    _('Cannot edit connection %s: '
                      'Connection type not supported.') % name)
            return redirect(reverse_lazy('network:index'))
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
        _activate_connection(name)
    except ConnectionNotFound as cnf:
        messages.error(request, cnf)
        return redirect(reverse_lazy('network:index'))
    except DeviceNotFound as dnf:
        messages.error(request, dnf)
        return redirect(reverse_lazy('network:index'))

    messages.success(request, _('Activated connection %s.') % name)
    return redirect(reverse_lazy('network:index'))


@login_required
def deactivate(request, conn_id):
    """Deactivate the connection."""
    name = urllib.parse.unquote_plus(conn_id)
    try:
        _deactivate_connection(name)
        messages.success(request, _('Deactivated connection %s.') % name)
    except ConnectionNotFound as cnf:
        messages.error(request, cnf)
    return redirect(reverse_lazy('network:index'))


@login_required
def add(request):
    """Serve the connection type selection form."""
    form = None

    if request.method == 'POST':
        form = ConnectionTypeSelectForm(request.POST)
        if form.is_valid():
            conn_type = form.cleaned_data['conn_type']
            if conn_type == '802-3-ethernet':
                return redirect(reverse_lazy('network:add_ethernet'))
            elif conn_type == '802-11-wireless':
                return redirect(reverse_lazy('network:add_wifi'))
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

            _add_ethernet_connection(name, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('network:index'))
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

            _add_wifi_connection(name, ssid, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('network:index'))
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
            _delete_connection(name)
        except ConnectionNotFound as cnf:
            messages.error(request, cnf)
        else:
            messages.success(request, _('Connection %s deleted.') % name)
        return redirect(reverse_lazy('network:index'))

    return TemplateResponse(request, 'connections_delete.html',
                            {'title': _('Delete Connection'),
                             'subsubmenu': subsubmenu,
                             'name': name})


class ConnectionNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


class DeviceNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


def get_connection_list():
    """Get a list of active and available connections."""
    connections = []
    active = []

    for conn in NetworkManager.NetworkManager.ActiveConnections:
        try:
            settings = conn.Connection.GetSettings()['connection']
        except DBusException:
            # DBusException can be thrown here if the index is quickly loaded
            # after a connection is deactivated.
            continue
        active.append(settings['id'])

    for conn in NetworkManager.Settings.ListConnections():
        settings = conn.GetSettings()['connection']
        # Display a friendly type name if known.
        conn_type = CONNECTION_TYPE_NAMES.get(settings['type'],
                                              settings['type'])
        connections.append({
            'name': settings['id'],
            'id': urllib.parse.quote_plus(settings['id']),
            'type': conn_type,
            'is_active': settings['id'] in active,
        })
    connections.sort(key=lambda x: x['is_active'], reverse=True)
    return connections


def get_connection(name):
    """Returns connection with id matching name.
    Returns None if not found.
    """
    connections = NetworkManager.Settings.ListConnections()
    connections = dict([(x.GetSettings()['connection']['id'], x)
                        for x in connections])
    return connections.get(name)


def get_active_connection(name):
    """Returns active connection with id matching name.
    Returns None if not found.
    """
    connections = NetworkManager.NetworkManager.ActiveConnections
    connections = dict([(x.Connection.GetSettings()['connection']['id'], x)
                        for x in connections])
    return connections.get(name)


def _edit_ethernet_connection(conn, name, ipv4_method, ipv4_address):
    settings = conn.GetSettings()

    new_settings = {
        'connection': {
            'id': name,
            'type': settings['connection']['type'],
            'uuid': settings['connection']['uuid'],
        },
        '802-3-ethernet': {},
        'ipv4': {'method': ipv4_method},
    }
    if ipv4_method == 'manual' and ipv4_address:
        new_settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    conn.Update(new_settings)


def _edit_wifi_connection(conn, name, ssid, ipv4_method, ipv4_address):
    settings = conn.GetSettings()

    new_settings = {
        'connection': {
            'id': name,
            'type': settings['connection']['type'],
            'uuid': settings['connection']['uuid'],
        },
        '802-11-wireless': {
            'ssid': ssid,
        },
        'ipv4': {'method': ipv4_method},
    }
    if ipv4_method == 'manual' and ipv4_address:
        new_settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    conn.Update(new_settings)


def _activate_connection(name):
    # Find the connection
    conn = get_connection(name)
    if not conn:
        raise ConnectionNotFound(
            _('Failed to activate connection %s: '
              'Connection not found.') % name)

    # Find a suitable device
    ctype = conn.GetSettings()['connection']['type']
    if ctype == 'vpn':
        for dev in NetworkManager.NetworkManager.GetDevices():
            if (dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED
                and dev.Managed):
                break
        else:
            raise DeviceNotFound(
                _('Failed to activate connection %s: '
                  'No suitable device is available.') % name)
    else:
        dtype = {
            '802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI,
            '802-3-ethernet': NetworkManager.NM_DEVICE_TYPE_ETHERNET,
            'gsm': NetworkManager.NM_DEVICE_TYPE_MODEM,
        }.get(ctype, ctype)

        for dev in NetworkManager.NetworkManager.GetDevices():
            if (dev.DeviceType == dtype
                and dev.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED):
                break
        else:
            raise DeviceNotFound(
                _('Failed to activate connection %s: '
                  'No suitable device is available.') % name)

    NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")


def _deactivate_connection(name):
    active = get_active_connection(name)
    if active:
        NetworkManager.NetworkManager.DeactivateConnection(active)
    else:
        raise ConnectionNotFound(
            _('Failed to deactivate connection %s: '
              'Connection not found.') % name)


def _add_ethernet_connection(name, ipv4_method, ipv4_address):
    conn = {
        'connection': {
            'id': name,
            'type': '802-3-ethernet',
            'uuid': str(uuid.uuid4()),
        },
        '802-3-ethernet': {},
        'ipv4': {'method': ipv4_method},
    }

    if ipv4_method == 'manual':
        conn['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    NetworkManager.Settings.AddConnection(conn)


def _add_wifi_connection(name, ssid, ipv4_method, ipv4_address):
    conn = {
        'connection': {
            'id': name,
            'type': '802-11-wireless',
            'uuid': str(uuid.uuid4()),
        },
        '802-11-wireless': {
            'ssid': ssid,
        },
        'ipv4': {'method': ipv4_method},
    }

    if ipv4_method == 'manual':
        conn['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    NetworkManager.Settings.AddConnection(conn)


def _delete_connection(name):
    conn = get_connection(name)
    if not conn:
        raise ConnectionNotFound(
            _('Failed to delete connection %s: '
              'Connection not found.') % name)
    conn.Delete()
