# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView

from plinth import kvstore, network
from plinth.modules import first_boot, networks

from .forms import (ConnectionTypeSelectForm, EthernetForm, GenericForm,
                    InternetConnectionTypeForm, PPPoEForm,
                    RouterConfigurationForm, WifiForm)

logger = logging.getLogger(__name__)


def index(request):
    """Show connection list."""
    connections = network.get_connection_list()

    internet_connection_type = kvstore.get_default(
        networks.INTERNET_CONNECTION_TYPE_KEY, 'unknown')
    return TemplateResponse(
        request, 'networks_configuration.html', {
            'app_id': 'networks',
            'app_info': networks.app.info,
            'title': _('Network Connections'),
            'has_diagnostics': True,
            'is_enabled': True,
            'connections': connections,
            'internet_connectivity_type': internet_connection_type
        })


def show(request, uuid):
    """Serve connection information."""
    try:
        connection = network.get_connection(uuid)
    except network.ConnectionNotFound:
        messages.error(request,
                       _('Cannot show connection: '
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

    return TemplateResponse(
        request, 'connection_show.html', {
            'title': _('Connection Information'),
            'connection': connection_status,
            'active_connection': active_connection_status,
            'device': device_status,
            'access_point': access_point_status
        })


def edit(request, uuid):
    """Serve connection editing form."""
    try:
        connection = network.get_connection(uuid)
    except network.ConnectionNotFound:
        messages.error(request,
                       _('Cannot edit connection: '
                         'Connection not found.'))
        return redirect(reverse_lazy('networks:index'))

    if connection.get_connection_type() not in network.CONNECTION_TYPE_NAMES:
        messages.error(request,
                       _('This type of connection is not yet understood.'))
        return redirect(reverse_lazy('networks:index'))

    form = None
    form_data = {'name': connection.get_id()}

    if request.method == 'POST':
        if connection.get_connection_type() == 'generic':
            form = GenericForm(request.POST)
        elif connection.get_connection_type() == '802-11-wireless':
            form = WifiForm(request.POST)
        elif connection.get_connection_type() == '802-3-ethernet':
            form = EthernetForm(request.POST)
        elif connection.get_connection_type() == 'pppoe':
            form = PPPoEForm(request.POST)

        if form.is_valid():
            network.edit_connection(connection, form.get_settings())

            return redirect(reverse_lazy('networks:index'))
        else:
            return TemplateResponse(request, 'connections_edit.html', {
                'title': _('Edit Connection'),
                'form': form
            })
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
            if settings_ipv4.get_num_addresses():
                address = settings_ipv4.get_address(0)
                form_data['ipv4_address'] = address.get_address()
                prefix = address.get_prefix()
                netmask = network.nm.utils_ip4_prefix_to_netmask(prefix)
                form_data['ipv4_netmask'] = network.ipv4_int_to_string(netmask)

            gateway = settings_ipv4.get_gateway()
            if gateway:
                form_data['ipv4_gateway'] = gateway

            number_of_dns = settings_ipv4.get_num_dns()
            if number_of_dns:
                form_data['ipv4_dns'] = settings_ipv4.get_dns(0)

            if number_of_dns > 1:
                form_data['ipv4_second_dns'] = settings_ipv4.get_dns(1)

            settings_ipv6 = connection.get_setting_ip6_config()
            form_data['ipv6_method'] = settings_ipv6.get_method()
            if settings_ipv6.get_num_addresses():
                address = settings_ipv6.get_address(0)
                form_data['ipv6_address'] = address.get_address()
                form_data['ipv6_prefix'] = address.get_prefix()

            gateway = settings_ipv6.get_gateway()
            if gateway:
                form_data['ipv6_gateway'] = gateway

            number_of_dns = settings_ipv6.get_num_dns()
            if number_of_dns:
                form_data['ipv6_dns'] = settings_ipv6.get_dns(0)

            if number_of_dns > 1:
                form_data['ipv6_second_dns'] = settings_ipv6.get_dns(1)

        if settings_connection.get_connection_type() == 'generic':
            form = GenericForm(form_data)
        elif settings_connection.get_connection_type() == '802-11-wireless':
            settings_wireless = connection.get_setting_wireless()
            form_data['ssid'] = settings_wireless.get_ssid().get_data()
            form_data['mode'] = settings_wireless.get_mode()
            form_data['band'] = settings_wireless.get_band() or 'auto'
            form_data['channel'] = settings_wireless.get_channel()
            form_data['bssid'] = settings_wireless.get_bssid()
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

            form = WifiForm(form_data)
        elif settings_connection.get_connection_type() == '802-3-ethernet':
            form = EthernetForm(form_data)
        elif settings_connection.get_connection_type() == 'pppoe':
            settings_pppoe = connection.get_setting_pppoe()
            form_data['username'] = settings_pppoe.get_username()
            secrets = connection.get_secrets('pppoe')
            form_data['password'] = secrets['pppoe']['password']
            form = PPPoEForm(form_data)

        return TemplateResponse(request, 'connections_edit.html', {
            'title': _('Edit Connection'),
            'form': form
        })


@require_POST
def activate(request, uuid):
    """Activate the connection."""
    try:
        connection = network.activate_connection(uuid)
        name = connection.get_id()
        messages.success(request,
                         _('Activated connection {name}.').format(name=name))
    except network.ConnectionNotFound:
        messages.error(
            request,
            _('Failed to activate connection: '
              'Connection not found.'))
    except network.DeviceNotFound as exception:
        name = exception.args[0].get_id()
        messages.error(
            request,
            _('Failed to activate connection {name}: '
              'No suitable device is available.').format(name=name))

    return redirect(reverse_lazy('networks:index'))


@require_POST
def deactivate(request, uuid):
    """Deactivate the connection."""
    try:
        active_connection = network.deactivate_connection(uuid)
        name = active_connection.get_id()
        messages.success(request,
                         _('Deactivated connection {name}.').format(name=name))
    except network.ConnectionNotFound:
        messages.error(
            request,
            _('Failed to de-activate connection: '
              'Connection not found.'))

    return redirect(reverse_lazy('networks:index'))


def scan(request):
    """Show a list of nearby visible Wi-Fi access points."""
    access_points = network.wifi_scan()
    return TemplateResponse(request, 'wifi_scan.html', {
        'title': _('Nearby Wi-Fi Networks'),
        'access_points': access_points
    })


def add(request):
    """Serve the connection type selection form."""
    form = None

    if request.method == 'POST':
        form = ConnectionTypeSelectForm(request.POST)
        if form.is_valid():
            connection_type = form.cleaned_data['connection_type']
            if connection_type == 'generic':
                return redirect(reverse_lazy('networks:add_generic'))
            elif connection_type == '802-3-ethernet':
                return redirect(reverse_lazy('networks:add_ethernet'))
            elif connection_type == '802-11-wireless':
                return redirect(reverse_lazy('networks:add_wifi'))
            elif connection_type == 'pppoe':
                return redirect(reverse_lazy('networks:add_pppoe'))
    else:
        form = ConnectionTypeSelectForm()
        return TemplateResponse(request, 'connections_type_select.html', {
            'title': _('Add Connection'),
            'form': form
        })


def add_generic(request):
    """Serve generic connection create form."""
    form = None

    if request.method == 'POST':
        form = GenericForm(request.POST)
        if form.is_valid():
            network.add_connection(form.get_settings())
            return redirect(reverse_lazy('networks:index'))
    else:
        form = GenericForm()

    return TemplateResponse(request, 'connections_create.html', {
        'title': _('Adding New Generic Connection'),
        'form': form
    })


def add_ethernet(request):
    """Serve ethernet connection create form."""
    form = None

    if request.method == 'POST':
        form = EthernetForm(request.POST)
        if form.is_valid():
            network.add_connection(form.get_settings())
            return redirect(reverse_lazy('networks:index'))
    else:
        form = EthernetForm()

    return TemplateResponse(request, 'connections_create.html', {
        'title': _('Adding New Ethernet Connection'),
        'form': form
    })


def add_pppoe(request):
    """Serve pppoe connection create form."""
    form = None

    if request.method == 'POST':
        form = PPPoEForm(request.POST)
        if form.is_valid():
            network.add_connection(form.get_settings())
            return redirect(reverse_lazy('networks:index'))
    else:
        form = PPPoEForm()

    return TemplateResponse(request, 'connections_create.html', {
        'title': _('Adding New PPPoE Connection'),
        'form': form
    })


def add_wifi(request, ssid=None, interface_name=None):
    """Serve wifi connection create form."""
    form = None
    form_data = None

    if ssid:
        device = network.get_device_by_interface_name(interface_name)
        form_data = {
            'name': ssid,
            'interface': interface_name if device else None,
            'zone': 'external',
            'ssid': ssid,
            'mode': 'infrastructure',
            'band': 'auto',
            'auth_mode': 'wpa',
            'ipv4_method': 'auto'
        }

    if request.method == 'POST':
        form = WifiForm(request.POST)
        if form.is_valid():
            network.add_connection(form.get_settings())
            return redirect(reverse_lazy('networks:index'))
    else:
        if form_data:
            form = WifiForm(form_data)
        else:
            form = WifiForm()

    return TemplateResponse(request, 'connections_create.html', {
        'title': _('Adding New Wi-Fi Connection'),
        'form': form
    })


def delete(request, uuid):
    """Handle deleting connections, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the connection.
    """
    if request.method == 'POST':
        try:
            name = network.delete_connection(uuid)
            messages.success(request,
                             _('Connection {name} deleted.').format(name=name))
        except network.ConnectionNotFound:
            messages.error(
                request,
                _('Failed to delete connection: '
                  'Connection not found.'))

        return redirect(reverse_lazy('networks:index'))

    try:
        connection = network.get_connection(uuid)
        name = connection.get_id()
    except network.ConnectionNotFound:
        messages.error(
            request, _('Failed to delete connection: '
                       'Connection not found.'))
        return redirect(reverse_lazy('networks:index'))

    return TemplateResponse(request, 'connections_delete.html', {
        'title': _('Delete Connection'),
        'name': name
    })


class RouterConfigurationView(FormView):
    """View for router configuration form."""
    template_name = 'router_configuration_update.html'
    form_class = RouterConfigurationForm
    success_url = reverse_lazy('networks:index')

    def get_initial(self):
        """Return initial data for the form."""
        return {
            'router_config':
                kvstore.get_default(networks.ROUTER_CONFIGURATION_TYPE_KEY,
                                    'not_configured')
        }

    def form_valid(self, form):
        """Save value to DB and redirect."""
        type_ = form.cleaned_data['router_config']
        logger.info('Updating router configuration: %s', type_)
        kvstore.set(networks.ROUTER_CONFIGURATION_TYPE_KEY, type_)
        return super().form_valid(form)


class RouterConfigurationFirstBootView(RouterConfigurationView):
    """View for router configuration form during first wizard."""
    template_name = 'router_configuration_firstboot.html'

    def get_success_url(self):
        """Return the next wizard step after this one."""
        return reverse_lazy(first_boot.next_step())

    def form_valid(self, form):
        """Mark the first wizard step as done, save value and redirect."""
        first_boot.mark_step_done('router_setup_wizard')
        if 'skip' in form.data:
            return FormView.form_valid(self, form)

        return super().form_valid(form)


class InternetConnectionTypeView(FormView):
    """View for Internet connection type form."""
    template_name = 'internet_connectivity_type.html'
    form_class = InternetConnectionTypeForm
    success_url = reverse_lazy('networks:index')

    def get_initial(self):
        """Return initial data for the form."""
        return {
            'internet_connection_type':
                kvstore.get_default(networks.INTERNET_CONNECTION_TYPE_KEY,
                                    'unknown')
        }

    def form_valid(self, form):
        """Save value to DB and redirect."""
        type_ = form.cleaned_data['internet_connection_type']
        logger.info('Updating internet connectivity type: %s', type_)
        kvstore.set(networks.INTERNET_CONNECTION_TYPE_KEY, type_)
        return super().form_valid(form)


class InternetConnectionTypeFirstBootView(InternetConnectionTypeView):
    """View to show Internet connection type form during first wizard."""
    template_name = 'internet_connectivity_firstboot.html'

    def get_success_url(self):
        """Return the next wizard step after this one."""
        return reverse_lazy(first_boot.next_step())

    def form_valid(self, form):
        """Mark the first wizard step as done, save value and redirect."""
        first_boot.mark_step_done('internet_connectivity_type_wizard')
        if 'skip' in form.data:
            return FormView.form_valid(self, form)

        return super().form_valid(form)
