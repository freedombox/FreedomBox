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
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from gettext import gettext as _
from logging import Logger

from .forms import (ConnectionTypeSelectForm, AddEthernetForm, AddPPPoEForm,
                    AddWifiForm)
from plinth import cfg
from plinth import network
from plinth import package


logger = Logger(__name__)

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


@package.required(['network-manager'])
def index(request):
    """Show connection list."""
    connections = network.get_connection_list()

    return TemplateResponse(request, 'connections_list.html',
                            {'title': _('Network Connections'),
                             'subsubmenu': subsubmenu,
                             'connections': connections})


def show(request, uuid):
    """Serve connection information."""
    try:
        connection = network.get_connection(uuid)
    except network.ConnectionNotFound:
        messages.error(request, _('Cannot show connection: '
                                  'Connection not found.'))
        return redirect(reverse_lazy('networks:index'))

    # Connection status
    connection_status = network.get_status_from_connection(connection)

    # Active connection status
    try:
        active_connection = network.get_active_connection(uuid)
        active_connection_status = \
            network.get_status_from_active_connection(active_connection)
    except network.ConnectionNotFound:
        active_connection_status = {}
        active_connection = None

    # Device status
    device = None
    if active_connection and active_connection.get_devices():
        device = active_connection.get_devices()[0]
    else:
        interface_name = connection_status['interface_name']
        if interface_name:
            device = network.get_device_by_interface_name(interface_name)

    device_status = network.get_status_from_device(device)

    # Access point status
    access_point_status = None
    if connection_status['type'] == '802-11-wireless':
        access_point_status = network.get_status_from_wifi_access_point(
            device, connection_status['wireless']['ssid'])

    return TemplateResponse(request, 'connection_show.html',
                            {'title': _('Show Connection information'),
                             'subsubmenu': subsubmenu,
                             'connection': connection_status,
                             'active_connection': active_connection_status,
                             'device': device_status,
                             'access_point': access_point_status})


def edit(request, uuid):
    """Serve connection editing form."""
    try:
        connection = network.get_connection(uuid)
    except network.ConnectionNotFound:
        messages.error(request, _('Cannot edit connection: '
                                  'Connection not found.'))
        return redirect(reverse_lazy('networks:index'))

    if connection.get_connection_type() not in network.CONNECTION_TYPE_NAMES:
        messages.error(request,
                       _('This type of connection is not yet understood.'))
        return redirect(reverse_lazy('networks:index'))

    form = None
    form_data = {'name': connection.get_id()}

    if request.method == 'POST':
        if connection.get_connection_type() == '802-11-wireless':
            form = AddWifiForm(request.POST)
        elif connection.get_connection_type() == '802-3-ethernet':
            form = AddEthernetForm(request.POST)
        elif connection.get_connection_type() == 'pppoe':
            form = AddPPPoEForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            interface = form.cleaned_data['interface']
            zone = form.cleaned_data['zone']
            if connection.get_connection_type() == 'pppoe':
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
            else:
                ipv4_method = form.cleaned_data['ipv4_method']
                ipv4_address = form.cleaned_data['ipv4_address']

            if connection.get_connection_type() == '802-3-ethernet':
                network.edit_ethernet_connection(
                    connection, name, interface, zone, ipv4_method,
                    ipv4_address)
            elif connection.get_connection_type() == '802-11-wireless':
                ssid = form.cleaned_data['ssid']
                mode = form.cleaned_data['mode']
                auth_mode = form.cleaned_data['auth_mode']
                passphrase = form.cleaned_data['passphrase']

                network.edit_wifi_connection(
                    connection, name, interface, zone, ssid, mode, auth_mode,
                    passphrase, ipv4_method, ipv4_address)
            elif connection.get_connection_type() == 'pppoe':
                network.edit_pppoe_connection(
                    connection, name, interface, zone, username, password)

            return redirect(reverse_lazy('networks:index'))
        else:
            return TemplateResponse(request, 'connections_edit.html',
                                    {'title': _('Edit Connection'),
                                     'subsubmenu': subsubmenu,
                                     'form': form})
    else:
        settings_connection = connection.get_setting_connection()
        form_data['interface'] = connection.get_interface_name()
        try:
            form_data['zone'] = settings_connection.get_zone()
        except KeyError:
            form_data['zone'] = 'external'

        if settings_connection.get_connection_type() != 'pppoe':
            settings_ipv4 = connection.get_setting_ip4_config()
            form_data['ipv4_method'] = settings_ipv4.get_method()
            address = network.get_first_ip_address_from_connection(connection)
            if address:
                form_data['ipv4_address'] = address

        if settings_connection.get_connection_type() == '802-11-wireless':
            settings_wireless = connection.get_setting_wireless()
            form_data['ssid'] = settings_wireless.get_ssid().get_data()
            form_data['mode'] = settings_wireless.get_mode()
            try:
                wifi_sec = connection.get_setting_wireless_security()
                if wifi_sec:
                    if wifi_sec.get_key_mgmt() == 'wpa-psk':
                        form_data['auth_mode'] = 'wpa'
                        secrets = connection.get_secrets(
                            '802-11-wireless-security')
                        psk = secrets['802-11-wireless-security']['psk']
                        form_data['passphrase'] = psk
                else:
                    form_data['auth_mode'] = 'open'
            except KeyError:
                form_data['auth_mode'] = 'open'

            form = AddWifiForm(form_data)
        elif settings_connection.get_connection_type() == '802-3-ethernet':
            form = AddEthernetForm(form_data)
        elif settings_connection.get_connection_type() == 'pppoe':
            settings_pppoe = connection.get_setting_pppoe()
            form_data['username'] = settings_pppoe.get_username()
            secrets = connection.get_secrets('pppoe')
            form_data['password'] = secrets['pppoe']['password']
            form = AddPPPoEForm(form_data)

        return TemplateResponse(request, 'connections_edit.html',
                                {'title': _('Edit Connection'),
                                 'subsubmenu': subsubmenu,
                                 'form': form})


@require_POST
def activate(request, uuid):
    """Activate the connection."""
    try:
        connection = network.activate_connection(uuid)
        name = connection.get_id()
        messages.success(request, _('Activated connection %s.') % name)
    except network.ConnectionNotFound:
        messages.error(request, _('Failed to activate connection: '
                                  'Connection not found.'))
    except network.DeviceNotFound as exception:
        name = exception.args[0].get_id()
        messages.error(request, _('Failed to activate connection %s: '
                                  'No suitable device is available.') % name)

    return redirect(reverse_lazy('networks:index'))


@require_POST
def deactivate(request, uuid):
    """Deactivate the connection."""
    try:
        active_connection = network.deactivate_connection(uuid)
        name = active_connection.get_id()
        messages.success(request, _('Deactivated connection %s.') % name)
    except network.ConnectionNotFound:
        messages.error(request, _('Failed to de-activate connection: '
                                  'Connection not found.'))

    return redirect(reverse_lazy('networks:index'))


def scan(request):
    """Show a list of nearby visible Wi-Fi access points."""
    access_points = network.wifi_scan()
    return TemplateResponse(request, 'wifi_scan.html',
                            {'title': _('Nearby Wi-Fi Networks'),
                             'subsubmenu': subsubmenu,
                             'access_points': access_points})


def add(request):
    """Serve the connection type selection form."""
    form = None

    if request.method == 'POST':
        form = ConnectionTypeSelectForm(request.POST)
        if form.is_valid():
            connection_type = form.cleaned_data['connection_type']
            if connection_type == '802-3-ethernet':
                return redirect(reverse_lazy('networks:add_ethernet'))
            elif connection_type == '802-11-wireless':
                return redirect(reverse_lazy('networks:add_wifi'))
            elif connection_type == 'pppoe':
                return redirect(reverse_lazy('networks:add_pppoe'))
    else:
        form = ConnectionTypeSelectForm()
        return TemplateResponse(request, 'connections_type_select.html',
                                {'title': _('Add Connection'),
                                 'subsubmenu': subsubmenu,
                                 'form': form})


def add_ethernet(request):
    """Serve ethernet connection create form."""
    form = None

    if request.method == 'POST':
        form = AddEthernetForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            interface = form.cleaned_data['interface']
            zone = form.cleaned_data['zone']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            network.add_ethernet_connection(
                name, interface, zone, ipv4_method, ipv4_address)
            return redirect(reverse_lazy('networks:index'))
    else:
        form = AddEthernetForm()

    return TemplateResponse(request, 'connections_create.html',
                            {'title': _('Adding New Ethernet Connection'),
                             'subsubmenu': subsubmenu,
                             'form': form})


def add_pppoe(request):
    """Serve pppoe connection create form."""
    form = None

    if request.method == 'POST':
        form = AddPPPoEForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            interface = form.cleaned_data['interface']
            zone = form.cleaned_data['zone']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            network.add_pppoe_connection(
                name, interface, zone, username, password)
            return redirect(reverse_lazy('networks:index'))
    else:
        form = AddPPPoEForm()

    return TemplateResponse(request, 'connections_create.html',
                            {'title': _('Adding New PPPoE Connection'),
                             'subsubmenu': subsubmenu,
                             'form': form})


def add_wifi(request, ssid=None, interface_name=None):
    """Serve wifi connection create form."""
    form = None
    form_data = None

    if ssid:
        device = network.get_device_by_interface_name(interface_name)
        form_data = {'name': ssid,
                     'interface': interface_name if device else None,
                     'zone': 'external',
                     'ssid': ssid,
                     'mode': 'infrastructure',
                     'auth_mode': 'wpa',
                     'ipv4_method': 'auto'}

    if request.method == 'POST':
        form = AddWifiForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            interface = form.cleaned_data['interface']
            zone = form.cleaned_data['zone']
            ssid = form.cleaned_data['ssid']
            mode = form.cleaned_data['mode']
            auth_mode = form.cleaned_data['auth_mode']
            passphrase = form.cleaned_data['passphrase']
            ipv4_method = form.cleaned_data['ipv4_method']
            ipv4_address = form.cleaned_data['ipv4_address']

            network.add_wifi_connection(
                name, interface, zone, ssid, mode, auth_mode, passphrase,
                ipv4_method, ipv4_address)
            return redirect(reverse_lazy('networks:index'))
    else:
        if form_data:
            form = AddWifiForm(form_data)
        else:
            form = AddWifiForm()

    return TemplateResponse(request, 'connections_create.html',
                            {'title': _('Adding New Wi-Fi Connection'),
                             'subsubmenu': subsubmenu,
                             'form': form})


def delete(request, uuid):
    """Handle deleting connections, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the connection.
    """
    if request.method == 'POST':
        try:
            name = network.delete_connection(uuid)
            messages.success(request, _('Connection %s deleted.') % name)
        except network.ConnectionNotFound:
            messages.error(request, _('Failed to delete connection: '
                                      'Connection not found.'))

        return redirect(reverse_lazy('networks:index'))

    try:
        connection = network.get_connection(uuid)
        name = connection.get_id()
    except network.ConnectionNotFound:
        messages.error(request, _('Failed to delete connection: '
                                  'Connection not found.'))
        return redirect(reverse_lazy('networks:index'))

    return TemplateResponse(request, 'connections_delete.html',
                            {'title': _('Delete Connection'),
                             'subsubmenu': subsubmenu,
                             'name': name})
