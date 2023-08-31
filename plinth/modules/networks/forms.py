# SPDX-License-Identifier: AGPL-3.0-or-later

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _

from plinth import cfg, network
from plinth.utils import format_lazy, import_from_gi

nm = import_from_gi('NM', '1.0')


class ConnectionTypeSelectForm(forms.Form):
    """Form to select type for new connection."""
    connection_type = forms.ChoiceField(
        label=_('Connection Type'), widget=forms.RadioSelect,
        choices=[(key, value)
                 for key, value in network.CONNECTION_TYPE_NAMES.items()])


class ConnectionForm(forms.Form):
    """Base form to create/edit a connection."""
    name = forms.CharField(label=_('Connection Name'))
    interface = forms.ChoiceField(
        label=_('Network Interface'), choices=(),
        help_text=_('The network device that this connection should be bound '
                    'to.'))
    zone = forms.ChoiceField(
        label=_('Firewall Zone'),
        help_text=_('The firewall zone will control which services are '
                    'available over this interfaces. Select Internal only '
                    'for trusted networks.'), choices=network.ZONES)
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'), widget=forms.RadioSelect, choices=[
            ('auto',
             _('Automatic (DHCP): Configure automatically, use Internet '
               'connection from this network')),
            ('shared',
             _('Shared: Act as a router, provide Internet connection to other '
               'devices on this network')),
            ('manual',
             _('Manual: Use manually specified parameters, use Internet '
               'connection from this network')),
            ('disabled',
             _('Disabled: Do not configure this addressing method')),
        ], initial='auto')

    ipv4_address = forms.CharField(
        label=_('Address'), validators=[validators.validate_ipv4_address],
        required=False)
    ipv4_netmask = forms.CharField(
        label=_('Netmask'),
        help_text=_('Optional value. If left blank, a default netmask '
                    'based on the address will be used.'),
        validators=[validators.validate_ipv4_address], required=False)
    ipv4_gateway = forms.CharField(
        label=_('Gateway'), help_text=_('Optional value.'),
        validators=[validators.validate_ipv4_address], required=False)
    ipv4_dns = forms.CharField(
        label=_('DNS Server'),
        help_text=_('Optional value. If this value is given and IPv4 '
                    'addressing method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv4_address], required=False)
    ipv4_second_dns = forms.CharField(
        label=_('Second DNS Server'),
        help_text=_('Optional value. If this value is given and IPv4 '
                    'Addressing Method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv4_address], required=False)
    ipv6_method = forms.ChoiceField(
        label=_('IPv6 Addressing Method'), widget=forms.RadioSelect, choices=[
            ('auto',
             _('Automatic: Configure automatically, use Internet connection '
               'from this network')),
            ('dhcp',
             _('Automatic (DHCP only): Configure automatically, use Internet '
               'connection from this network')),
            ('manual',
             _('Manual: Use manually specified parameters, use Internet '
               'connection from this network')),
            ('ignore', _('Ignore: Ignore this addressing method')),
        ])
    ipv6_address = forms.CharField(
        label=_('Address'), validators=[validators.validate_ipv6_address],
        required=False)
    ipv6_prefix = forms.IntegerField(label=_('Prefix'),
                                     help_text=_('Value between 1 and 128.'),
                                     min_value=1, max_value=128,
                                     required=False)
    ipv6_gateway = forms.CharField(
        label=_('Gateway'), help_text=_('Optional value.'),
        validators=[validators.validate_ipv6_address], required=False)
    ipv6_dns = forms.CharField(
        label=_('DNS Server'),
        help_text=_('Optional value. If this value is given and IPv6 '
                    'addressing method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv6_address], required=False)
    ipv6_second_dns = forms.CharField(
        label=_('Second DNS Server'),
        help_text=_('Optional value. If this value is given and IPv6 '
                    'Addressing Method is "Automatic", the DNS Servers '
                    'provided by a DHCP server will be ignored.'),
        validators=[validators.validate_ipv6_address], required=False)

    @staticmethod
    def _get_interface_choices(device_type):
        """Return a list of choices for a given device type."""
        interfaces = network.get_interface_list(device_type)
        # Support for virtual Ethernet devices used in containers
        if device_type == nm.DeviceType.ETHERNET:
            interfaces.update(network.get_interface_list(nm.DeviceType.VETH))

        choices = [('', _('-- select --'))]
        for interface, mac in interfaces.items():
            display_string = '{interface} ({mac})'.format(
                interface=interface, mac=mac)
            choices.append((interface, display_string))

        return choices

    def get_settings(self):
        """Return settings dict from cleaned data."""
        settings = {}
        settings['common'] = {
            'name': self.cleaned_data['name'],
            'interface': self.cleaned_data['interface'],
            'zone': self.cleaned_data['zone'],
        }
        settings['ipv4'] = self.get_ipv4_settings()
        settings['ipv6'] = self.get_ipv6_settings()
        return settings

    def get_ipv4_settings(self):
        """Return IPv4 dict from cleaned data."""
        ipv4 = {
            'method': self.cleaned_data['ipv4_method'],
            'address': self.cleaned_data['ipv4_address'],
            'netmask': self.cleaned_data['ipv4_netmask'],
            'gateway': self.cleaned_data['ipv4_gateway'],
            'dns': self.cleaned_data['ipv4_dns'],
            'second_dns': self.cleaned_data['ipv4_second_dns'],
        }
        return ipv4

    def get_ipv6_settings(self):
        """Return IPv6 dict from cleaned data."""
        ipv6 = {
            'method': self.cleaned_data['ipv6_method'],
            'address': self.cleaned_data['ipv6_address'],
            'prefix': self.cleaned_data['ipv6_prefix'],
            'gateway': self.cleaned_data['ipv6_gateway'],
            'dns': self.cleaned_data['ipv6_dns'],
            'second_dns': self.cleaned_data['ipv6_second_dns'],
        }
        return ipv6


class GenericForm(ConnectionForm):
    """Form to create/edit a generic connection."""

    def __init__(self, *args, **kwargs):
        """Initialize the form, populate interface choices."""
        super().__init__(*args, **kwargs)
        choices = self._get_interface_choices(nm.DeviceType.GENERIC)
        self.fields['interface'].choices = choices

    def get_settings(self):
        """Return settings dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = 'generic'
        return settings


class EthernetForm(ConnectionForm):
    """Form to create/edit a ethernet connection."""

    def __init__(self, *args, **kwargs):
        """Initialize the form, populate interface choices."""
        super().__init__(*args, **kwargs)
        choices = self._get_interface_choices(nm.DeviceType.ETHERNET)
        self.fields['interface'].choices = choices

    def get_settings(self):
        """Return settings dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = '802-3-ethernet'
        return settings


class PPPoEForm(EthernetForm):
    """Form to create a new PPPoE connection."""
    ipv4_method = None
    ipv4_address = None
    ipv4_netmask = None
    ipv4_gateway = None
    ipv4_dns = None
    ipv4_second_dns = None
    ipv6_method = None
    ipv6_address = None
    ipv6_prefix = None
    ipv6_gateway = None
    ipv6_dns = None
    ipv6_second_dns = None

    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput(render_value=True))
    show_password = forms.BooleanField(label=_('Show password'),
                                       required=False)

    def get_settings(self):
        """Return setting dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = 'pppoe'
        settings['pppoe'] = {
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password'],
        }
        return settings

    def get_ipv4_settings(self):
        """Return IPv4 settings from cleaned data."""
        return None

    def get_ipv6_settings(self):
        """Return IPv6 settings from cleaned data."""
        return None


class WifiForm(ConnectionForm):
    """Form to create/edit a Wi-Fi connection."""
    field_order = [
        'name', 'interface', 'zone', 'ssid', 'mode', 'band', 'channel',
        'bssid', 'auth_mode', 'passphrase', 'ipv4_method', 'ipv4_address',
        'ipv4_netmask', 'ipv4_gateway', 'ipv4_dns', 'ipv4_second_dns',
        'ipv6_method', 'ipv6_address', 'ipv6_prefix', 'ipv6_gateway',
        'ipv6_dns', 'ipv6_second_dns'
    ]

    ssid = forms.CharField(label=_('SSID'),
                           help_text=_('The visible name of the network.'))
    mode = forms.ChoiceField(
        label=_('Mode'), choices=[('infrastructure', _('Infrastructure')),
                                  ('ap', _('Access Point')),
                                  ('adhoc', _('Ad-hoc'))])
    band = forms.ChoiceField(
        label=_('Frequency Band'), choices=[('auto', _('Automatic')),
                                            ('a', _('A (5 GHz)')),
                                            ('bg', _('B/G (2.4 GHz)'))])
    channel = forms.IntegerField(
        label=_('Channel'),
        help_text=_('Optional value. Wireless channel in the selected '
                    'frequency band to restrict to. Blank or 0 value means '
                    'automatic selection.'), min_value=0, max_value=255,
        required=False)
    bssid = forms.RegexField(
        label=_('BSSID'),
        help_text=_('Optional value. Unique identifier for the access point. '
                    'When connecting to an access point, connect only if the '
                    'BSSID of the access point matches the one provided. '
                    'Example: 00:11:22:aa:bb:cc.'),
        regex=r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', required=False)
    auth_mode = forms.ChoiceField(
        label=_('Authentication Mode'),
        help_text=_('Select WPA if the wireless network is secured and \
requires clients to have the password to connect.'),
        choices=[('wpa', _('WPA')), ('open', _('Open'))])
    passphrase = forms.CharField(label=_('Passphrase'),
                                 validators=[validators.MinLengthValidator(8)],
                                 required=False)

    def __init__(self, *args, **kwargs):
        """Initialize the form, populate interface choices."""
        super().__init__(*args, **kwargs)
        choices = self._get_interface_choices(nm.DeviceType.WIFI)
        self.fields['interface'].choices = choices

    def get_settings(self):
        """Return setting dict from cleaned data."""
        settings = super().get_settings()
        settings['common']['type'] = '802-11-wireless'
        settings['wireless'] = {
            'ssid': self.cleaned_data['ssid'],
            'mode': self.cleaned_data['mode'],
            'band': self.cleaned_data['band'],
            'channel': self.cleaned_data['channel'],
            'bssid': self.cleaned_data['bssid'],
            'auth_mode': self.cleaned_data['auth_mode'],
            'passphrase': self.cleaned_data['passphrase'],
        }
        return settings


class NetworkTopologyForm(forms.Form):
    """Form to ask the user for network topology.

    That is how the FreedomBox is connected to the internal network topology.
    Store this information for future suggestions when setting up services.

    """
    network_topology = forms.ChoiceField(
        label=format_lazy(
            _('Specify how your {box_name} is connected to your network'),
            box_name=cfg.box_name),
        required=True,
        widget=forms.RadioSelect,
        choices=[
            ('to_router',
             format_lazy(
                 _('Connected to a router '
                   '<p class="help-block">Your {box_name} gets its Internet '
                   'connection from your router via Wi-Fi or Ethernet cable. '
                   'This is a typical home setup.</p>'), box_name=cfg.box_name,
                 allow_markup=True)),
            ('as_router',
             format_lazy(
                 _('{box_name} is your router '
                   '<p class="help-block">Your {box_name} has multiple '
                   'network interfaces such as multiple Ethernet ports or '
                   'a Wi-Fi adapter. {box_name} is directly connected to the '
                   'Internet and all your devices connect to {box_name} '
                   'for their Internet connectivity.</p>'),
                 box_name=cfg.box_name, allow_markup=True)),
            ('direct',
             format_lazy(
                 _('Directly connected to the Internet '
                   '<p class="help-block">Your Internet connection is '
                   'directly attached to your {box_name} and there are no '
                   'other devices on the network. This can happen on '
                   'community or cloud setups.</p>'), box_name=cfg.box_name,
                 allow_markup=True)),
        ],
    )


class InternetConnectionTypeForm(forms.Form):
    """Form for type of public/private IP address ISP provides.

    Ask the user for what type of Internet connection they have. We store this
    information and use it suggest various setup options during the setup
    process and also later on when setting up apps.

    """
    internet_connection_type = forms.ChoiceField(
        label=_('Choose your internet connection type'),
        choices=[
            ('dynamic_public_ip',
             format_lazy(
                 _('I have a public IP address that may change over time'
                   '<p class="help-block">This means that devices on the '
                   'Internet can reach you when you are connected to the '
                   'Internet. Every time you connect to the Internet with '
                   'your Internet Service Provider (ISP), you may get a '
                   'different IP address, especially after some offline time. '
                   'Many ISPs offer this type of connectivity. If you have a '
                   'public IP address but are unsure if it changes over time '
                   'or not, it is safer to choose this option.</p>'),
                 allow_markup=True)),
            ('static_public_ip',
             format_lazy(
                 _('I have a public IP address that does not change over time '
                   '(recommended)'
                   '<p class="help-block">This means that devices on the '
                   'Internet can reach you when you are connected to the '
                   'Internet. Every time you connect to the Internet with '
                   'your Internet Service Provider (ISP), you always get the '
                   'same IP address. This is the most trouble-free setup for '
                   'many {box_name} services but very few ISPs offer this. '
                   'You may be able to get this service from your ISP by '
                   'making an additional payment.</p>'), box_name=cfg.box_name,
                 allow_markup=True)),
            ('private_ip',
             format_lazy(
                 _('I dont have a public IP address'
                   '<p class="help-block">This means that devices on the '
                   'Internet <b>can not</b> reach you when you are connected '
                   'to the Internet. Every time you connect to the Internet '
                   'with your Internet Service Provider (ISP), you get an IP '
                   'address that is only relevant for local networks. '
                   'Many ISPs offer this type of connectivity. This is the '
                   'most troublesome situation for hosting services at home. '
                   '{box_name} provides many workaround solutions but each '
                   'solution has some limitations.</p>'),
                 box_name=cfg.box_name, allow_markup=True)),
            ('unknown',
             format_lazy(
                 _('I do not know the type of connection my ISP provides '
                   '<p class="help-block">You will be suggested the most '
                   'conservative actions.</p>'), allow_markup=True)),
        ],
        required=True,
        widget=forms.RadioSelect,
    )


class RouterConfigurationForm(forms.Form):
    """Form to suggest how to configure a router.

    Suggest depending on wan connectivity/specific setup. The choice will
    affect future suggestions during the setup process and other apps.

    """
    router_config = forms.ChoiceField(
        label=_('Preferred router configuration'),
        choices=[
            (
                'dmz',
                format_lazy(
                    _('Use DMZ feature to forward all traffic (recommended) '
                      '<p class="help-block">Most routers provide a '
                      'configuration setting called DMZ. This will allow the '
                      'router to forward all incoming traffic from the '
                      'Internet to a single IP address such as the '
                      '{box_name}\'s IP address. First remember to configure '
                      'a static local IP address for your {box_name} in your '
                      'router\'s configuration.</p>'), box_name=cfg.box_name,
                    allow_markup=True),
            ),
            ('port_forwarding',
             format_lazy(
                 _('Forward specific traffic as needed by each '
                   'application '
                   '<p class="help-block">You may alternatively choose to '
                   'forward only specific traffic to your {box_name}. '
                   'This is ideal if you have other servers like '
                   '{box_name} in your network or if your router does not '
                   'support DMZ feature. All applications that provide a '
                   'web interface need you to forward traffic from ports '
                   '80 and 443 to work. Each of the other applications '
                   'will suggest which port(s) need to be forwarded '
                   'for that application to work.</p>'), box_name=cfg.box_name,
                 allow_markup=True)),
            ('not_configured',
             format_lazy(
                 _('Router is currently unconfigured '
                   '<p class="help-block">Choose this if you have not '
                   'configured or are unable to configure the router '
                   'currently and wish to be reminded later. Some of '
                   'the other configuration steps may fail.</p>'),
                 allow_markup=True)),
        ],
        required=True,
        widget=forms.RadioSelect,
    )
