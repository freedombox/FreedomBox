# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView

from plinth import network
from plinth.modules import first_boot, names, networks
from plinth.views import AppView

from .forms import (ConnectionTypeSelectForm, EthernetForm, GenericForm,
                    InternetConnectionTypeForm, NetworkTopologyForm, PPPoEForm,
                    RouterConfigurationForm, WifiForm)

logger = logging.getLogger(__name__)

# i18n for device.state
# https://developer.gnome.org/libnm/1.29/libnm-nm-dbus-interface.html#NMDeviceState
CONNECTION_METHOD_STRINGS = {
    'disabled': gettext_lazy('disabled'),
    'auto': gettext_lazy('automatic'),
    'manual': gettext_lazy('manual'),
    'shared': gettext_lazy('shared'),
    'link-local': gettext_lazy('link-local'),
    'dhcp': gettext_lazy('dhcp'),
    'ignore': gettext_lazy('ignore'),
}

# i18n for device.state
# https://developer.gnome.org/libnm/1.29/libnm-nm-dbus-interface.html#NMDeviceState
DEVICE_STATE_STRINGS = {
    'unknown': gettext_lazy('unknown'),
    'unmanaged': gettext_lazy('unmanaged'),
    'unavailable': gettext_lazy('unavailable'),
    'disconnected': gettext_lazy('disconnected'),
    'prepare': gettext_lazy('preparing'),
    'config': gettext_lazy('connecting'),
    'need-auth': gettext_lazy('needs authentication'),
    'ip-config': gettext_lazy('requesting address'),
    'ip-check': gettext_lazy('checking'),
    'secondaries': gettext_lazy('waiting for secondary'),
    'activated': gettext_lazy('activated'),
    'deactivating': gettext_lazy('deactivating'),
    'failed': gettext_lazy('failed'),
}

# i18n for device.state_reason
# https://developer.gnome.org/libnm/1.29/libnm-nm-dbus-interface.html#NMDeviceStateReason
DEVICE_STATE_REASON_STRINGS = {
    'none':
        gettext_lazy('no reason'),
    'unknown':
        gettext_lazy('unknown error'),
    'now-managed':
        gettext_lazy('device is now managed'),
    'now-unmanaged':
        gettext_lazy('device is now unmanaged'),
    'config-failed':
        gettext_lazy('configuration failed'),
    'no-secrets':
        gettext_lazy('secrets required'),
    'dhcp-start-failed':
        gettext_lazy('DHCP client failed to start'),
    'dhcp-error':
        gettext_lazy('DHCP client error'),
    'dhcp-failed':
        gettext_lazy('DHCP client failed'),
    'shared-start-failed':
        gettext_lazy('shared connection service failed to start'),
    'shared-failed':
        gettext_lazy('shared connection service failed'),
    'removed':
        gettext_lazy('device was removed'),
    'user-requested':
        gettext_lazy('device disconnected by user'),
    'dependency-failed':
        gettext_lazy('a dependency of the connection failed'),
    'ssid-not-found':
        gettext_lazy('Wi-Fi network not found'),
    'secondary-connection-failed':
        gettext_lazy('a secondary connection failed'),
    'new-activation':
        gettext_lazy('new connection activation was enqueued'),
    'ip-address-duplicate':
        gettext_lazy('a duplicate IP address was detected'),
    'ip-method-unsupported':
        gettext_lazy('selected IP method is not supported'),
}

# i18n for device.type
# https://developer.gnome.org/libnm/1.29/libnm-nm-dbus-interface.html#NMDeviceType
DEVICE_TYPE_STRINGS = {
    'unknown': gettext_lazy('unknown'),
    'ethernet': gettext_lazy('Ethernet'),
    'wifi': gettext_lazy('Wi-Fi'),
    'generic': gettext_lazy('generic'),
    'tun': gettext_lazy('TUN or TAP interface'),
    'wireguard': gettext_lazy('WireGuard'),
}

# i18n for wireless.mode
# https://developer.gnome.org/libnm/1.29/libnm-nm-dbus-interface.html#NM80211Mode
WIRELESS_MODE_STRINGS = {
    'unknown': gettext_lazy('unknown'),
    'adhoc': gettext_lazy('ad-hoc'),
    'infra': gettext_lazy('infrastructure'),
    'ap': gettext_lazy('access point'),
    'mesh': gettext_lazy('mesh point'),
}

# i18n for connection.dns_over_tls
# https://networkmanager.dev/docs/libnm/latest/NMSettingConnection.html#
# NMSettingConnectionDnsOverTls
DNS_OVER_TLS_STRINGS = {
    'default': gettext_lazy('default'),
    'no': gettext_lazy('no'),
    'opportunistic': gettext_lazy('opportunistic'),
    'yes': gettext_lazy('yes'),
}


class NetworksAppView(AppView):
    """Show networks app main page."""

    app_id = 'networks'
    template_name = 'networks_configuration.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        connections = network.get_connection_list()

        network_topology_type = networks.get_network_topology_type()
        internet_connection_type = networks.get_internet_connection_type()

        context = super().get_context_data(*args, **kwargs)
        context['connections'] = connections
        context['network_topology'] = network_topology_type
        context['internet_connectivity_type'] = internet_connection_type
        return context


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
    connection_status['zone_string'] = dict(network.ZONES).get(
        connection_status['zone'], connection_status['zone'])
    connection_status['dns_over_tls_string'] = DNS_OVER_TLS_STRINGS.get(
        connection_status['dns_over_tls'], connection_status['dns_over_tls'])
    connection_status['ipv4']['method_string'] = CONNECTION_METHOD_STRINGS.get(
        connection_status['ipv4']['method'],
        connection_status['ipv4']['method'])
    connection_status['ipv6']['method_string'] = CONNECTION_METHOD_STRINGS.get(
        connection_status['ipv6']['method'],
        connection_status['ipv6']['method'])

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
    device_status['state_string'] = DEVICE_STATE_STRINGS.get(
        device_status['state'], device_status['state'])
    device_status['state_reason_string'] = DEVICE_STATE_REASON_STRINGS.get(
        device_status['state_reason'], device_status['state_reason'])
    device_status['type_string'] = DEVICE_TYPE_STRINGS.get(
        device_status['type'], device_status['type'])

    # Access point status
    access_point_status = None
    if connection_status['type'] == '802-11-wireless':
        access_point_status = network.get_status_from_wifi_access_point(
            device, connection_status['wireless']['ssid'])
        connection_status['wireless'][
            'mode_string'] = WIRELESS_MODE_STRINGS.get(
                connection_status['wireless']['mode'],
                connection_status['wireless']['mode'])

    return TemplateResponse(
        request, 'connection_show.html', {
            'title': _('Connection Information'),
            'connection': connection_status,
            'active_connection': active_connection_status,
            'device': device_status,
            'access_point': access_point_status,
            'is_resolved_installed': names.is_resolved_installed()
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
            form_data['dns_over_tls'] = \
                settings_connection.get_dns_over_tls().value_nick

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


class NetworkTopologyView(FormView):
    """View for local network topology form."""
    template_name = 'network_topology_update.html'
    form_class = NetworkTopologyForm
    success_url = reverse_lazy('networks:index')

    def get_initial(self):
        """Get initial form data."""
        return {'network_topology': networks.get_network_topology_type()}

    def form_valid(self, form):
        """Save value to DB."""
        network_topology = form.cleaned_data['network_topology']
        logger.info('Updating network topology type with value %s' %
                    network_topology)
        networks.set_network_topology_type(network_topology)
        if network_topology == 'to_router':
            self.success_url = reverse_lazy('networks:router-configuration')

        return super().form_valid(form)


class NetworkTopologyFirstBootView(NetworkTopologyView):
    """View for network topology form during first wizard."""
    template_name = 'network_topology_firstboot.html'

    def get_success_url(self):
        """Return next fistboot step."""
        return reverse_lazy(first_boot.next_step())

    def form_valid(self, form):
        """Mark the first wizard step as done, save value and redirect."""
        first_boot.mark_step_done('network_topology_wizard')
        if 'skip' in form.data:
            first_boot.mark_step_done('router_setup_wizard')
            return FormView.form_valid(self, form)

        return super().form_valid(form)


class RouterConfigurationView(FormView):
    """View for router configuration form."""
    template_name = 'router_configuration_update.html'
    form_class = RouterConfigurationForm
    success_url = reverse_lazy('networks:index')

    def get_initial(self):
        """Return initial data for the form."""
        return {'router_config': networks.get_router_configuration_type()}

    def form_valid(self, form):
        """Save value to DB and redirect."""
        type_ = form.cleaned_data['router_config']
        logger.info('Updating router configuration: %s', type_)
        networks.set_router_configuration_type(type_)
        return super().form_valid(form)


class RouterConfigurationFirstBootView(RouterConfigurationView):
    """View for router configuration form during first wizard."""
    template_name = 'router_configuration_firstboot.html'

    def dispatch(self, request, *args, **kwargs):
        """Don't show wizard step if FreedomBox is not behind a router."""
        network_topology = networks.get_network_topology_type()
        if network_topology != 'to_router':
            first_boot.mark_step_done('router_setup_wizard')
            return HttpResponseRedirect(reverse_lazy(first_boot.next_step()))

        return super().dispatch(request, *args, *kwargs)

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
                networks.get_internet_connection_type()
        }

    def form_valid(self, form):
        """Save value to DB and redirect."""
        type_ = form.cleaned_data['internet_connection_type']
        logger.info('Updating internet connectivity type: %s', type_)
        networks.set_internet_connection_type(type_)
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
