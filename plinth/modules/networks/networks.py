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

    name = connection.get_interface_name()
    connectiontype = connection.get_connection_type()
    settings_ipv4 = connection.get_setting_ip4_config()

    mac = network.get_mac_from_device(name)
    interface = connection.get_interface_name()
    if connectiontype == '802-11-wireless':
        settings_wireless = connection.get_setting_wireless()
        ssid = settings_wireless.get_ssid().get_data()
        rate = network.get_wifi_rate(interface, ssid)
        channel = network.get_wifi_channel(interface, ssid)
        strength = network.get_wifi_signal(interface, ssid)
        linkstate = True
    else:
        ssid = "None"
        rate = 0
        channel = 0
        linkstate = network.get_linkstate_from_device(name)
        strength = 0

    ip = network.get_all_ip_from_device(name)
    ip6 = network.get_all_ip6_from_device(name)
    dns = network.get_namesever_from_device(name)
    dns6 = network.get_namesever6_from_device(name)
    gateway = network.get_gateway_from_device(name)
    gateway6 = network.get_gateway6_from_device(name)
    method = settings_ipv4.get_method()

    zone = connection.get_setting_connection().get_zone()
    active = network.connection_is_active(uuid)

    if network.get_primary_connection().get_id() == connection.get_id():
        primary = True
    else:
        primary = False

    if not ip:
        ip.append("0.0.0.0/0")

    if not ip6:
        ip6.append("::0/0")

    return TemplateResponse(request, 'connection_show.html',
                            {'title': _('Show Connection information'),
                             'ip': ip,
                             'ip6': ip6,
                             'gateway': gateway,
                             'gateway6': gateway6,
                             'dns': dns,
                             'dns6': dns6,
                             'interface': interface,
                             'mac': mac,
                             'linkstate': linkstate,
                             'zone': zone,
                             'primary': primary,
                             'subsubmenu': subsubmenu,
                             'method': method,
                             'connectiontype': connectiontype,
                             'ssid': ssid,
                             'strength': strength,
                             'rate': rate,
                             'channel': channel,
                             'active': active,
                             'uuid': uuid,
                             'name': name})


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

            name = connection.get_interface_name()
            form_data['ipv4_address'] = network.get_ip_from_device(name)

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


def add_wifi(request, ssid=None):
    """Serve wifi connection create form."""
    form = None
    form_data = None

    if ssid:
        device = network.get_first_wifi_device()
        form_data = {'name': ssid,
                     'interface': device,
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
