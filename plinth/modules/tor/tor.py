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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for configuring Tor
"""

import augeas
from django import forms
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
import glob
import itertools

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import package
from plinth.errors import ActionError
from plinth.modules.names import SERVICES
from plinth.signals import domain_added, domain_removed

APT_SOURCES_URI_PATHS = ('/files/etc/apt/sources.list/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/uri')
APT_TOR_PREFIX = 'tor+'


class TorForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form"""
    enabled = forms.BooleanField(
        label=_('Enable Tor'),
        required=False)
    hs_enabled = forms.BooleanField(
        label=_('Enable Tor Hidden Service'),
        required=False,
        help_text=_('A hidden service will allow FreedomBox to provide '
                    'selected services (such as ownCloud or Chat) without '
                    'revealing its location.'))
    apt_transport_tor_enabled = forms.BooleanField(
        label=_('Download software packages over Tor'),
        required=False,
        help_text=_('When enabled, software will be downloaded over the Tor '
                    'network for installations and upgrades. This adds a '
                    'degree of privacy and security during software '
                    'downloads.'))


def init():
    """Initialize the Tor module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Anonymity Network (Tor)'), 'glyphicon-eye-close',
                     'tor:index', 100)

    # Register hidden service name with Name Services module.
    enabled = action_utils.service_is_enabled('tor')
    is_running = action_utils.service_is_running('tor')
    (hs_enabled, hs_hostname, hs_ports) = get_hs()

    if enabled and is_running and hs_enabled and hs_hostname:
        hs_services = []
        for service in SERVICES:
            if str(service[2]) in hs_ports:
                hs_services.append(service[0])
    else:
        hs_hostname = None
        hs_services = None

    domain_added.send_robust(
        sender='tor', domain_type='hiddenservice',
        name=hs_hostname, description=_('Tor Hidden Service'),
        services=hs_services)


def on_install():
    """Setup Tor configuration as soon as it is installed."""
    actions.superuser_run('tor', ['setup'])
    actions.superuser_run('tor', ['enable-apt-transport-tor'])


@package.required(['tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy',
                   'apt-transport-tor'],
                  on_install=on_install)
def index(request):
    """Service the index page"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = TorForm(request.POST, prefix='tor')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = TorForm(initial=status, prefix='tor')
    else:
        form = TorForm(initial=status, prefix='tor')

    return TemplateResponse(request, 'tor.html',
                            {'title': _('Tor Control Panel'),
                             'status': status,
                             'form': form})


def get_augeas():
    """Return an instance of Augeaus for processing APT configuration."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Aptsources/lens', 'Aptsources.lns')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]', '/etc/apt/sources.list')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]',
            '/etc/apt/sources.list.d/*.list')
    aug.load()

    # Currently, augeas does not handle Deb822 format, it error out.
    if aug.match('/augeas/files/etc/apt/sources.list/error') or \
       aug.match('/augeas/files/etc/apt/sources.list.d//error'):
        raise Exception('Error parsing sources list')

    # Starting with Apt 1.1, /etc/apt/sources.list.d/*.sources will
    # contain files with Deb822 format.  If they are found, error out
    # for now.  XXX: Provide proper support Deb822 format with a new
    # Augeas lens.
    if glob.glob('/etc/apt/sources.list.d/*.sources'):
        raise Exception('Can not handle Deb822 source files')

    return aug


def iter_apt_uris(aug):
    """Iterate over all the APT source URIs."""
    return itertools.chain.from_iterable([aug.match(path)
                                          for path in APT_SOURCES_URI_PATHS])


def get_real_apt_uri_path(aug, path):
    """Return the actual path which contains APT URL.

    XXX: This is a workaround for Augeas bug parsing Apt source files
    with '[options]'.  Remove this workaround after Augeas lens is
    fixed.
    """
    uri = aug.get(path)
    if uri[0] == '[':
        parent_path = path.rsplit('/', maxsplit=1)[0]
        skipped = False
        for child_path in aug.match(parent_path + '/*')[1:]:
            if skipped:
                return child_path

            value = aug.get(child_path)
            if value[-1] == ']':
                skipped = True

    return path


def is_apt_transport_tor_enabled():
    """Return whether APT is set to download packages over Tor."""
    try:
        aug = get_augeas()
    except Exception:
        # If there was an error with parsing or there are Deb822
        # files.
        return False

    for uri_path in iter_apt_uris(aug):
        uri_path = get_real_apt_uri_path(aug, uri_path)
        uri = aug.get(uri_path)
        if not uri.startswith(APT_TOR_PREFIX) and \
           (uri.startswith('http://') or uri.startswith('https://')):
            return False

    return True


def get_hs():
    output = actions.superuser_run('tor', ['get-hs'])
    output = output.strip()
    if output == '':
        hs_enabled = False
        hs_hostname = 'Not Configured'
        hs_ports = ''
    elif output == 'error':
        hs_enabled = False
        hs_hostname = 'Not available (Run Tor at least once)'
        hs_ports = ''
    else:
        hs_enabled = True
        hs_info = output.split()
        hs_hostname = hs_info[0]
        hs_ports = hs_info[1]

    return (hs_enabled, hs_hostname, hs_ports)


def get_status():
    """Return the current status"""
    output = actions.superuser_run('tor', ['get-ports'])
    port_info = output.split('\n')
    ports = {}
    for line in port_info:
        try:
            (key, val) = line.split()
            ports[key] = val
        except ValueError:
            continue

    (hs_enabled, hs_hostname, hs_ports) = get_hs()

    return {'enabled': action_utils.service_is_enabled('tor'),
            'is_running': action_utils.service_is_running('tor'),
            'ports': ports,
            'hs_enabled': hs_enabled,
            'hs_hostname': hs_hostname,
            'hs_ports': hs_ports,
            'apt_transport_tor_enabled': is_apt_transport_tor_enabled()}


def _apply_changes(request, old_status, new_status):
    """Try to apply changes and handle errors."""
    try:
        __apply_changes(request, old_status, new_status)
    except ActionError as exception:
        messages.error(request, _('Action error: {0} [{1}] [{2}]').format(
            exception.args[0], exception.args[1], exception.args[2]))


def __apply_changes(request, old_status, new_status):
    """Apply the changes."""
    if old_status['enabled'] == new_status['enabled'] and \
       old_status['hs_enabled'] == new_status['hs_enabled'] and \
       old_status['apt_transport_tor_enabled'] == \
       new_status['apt_transport_tor_enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if old_status['enabled'] != new_status['enabled']:
        if new_status['enabled']:
            actions.superuser_run('tor', ['enable'])
            messages.success(request, _('Tor enabled'))
        else:
            actions.superuser_run('tor', ['disable'])
            messages.success(request, _('Tor disabled'))

    if old_status['hs_enabled'] != new_status['hs_enabled']:
        if new_status['hs_enabled']:
            actions.superuser_run('tor', ['enable-hs'])
            messages.success(request, _('Tor hidden service enabled'))
        else:
            actions.superuser_run('tor', ['disable-hs'])
            messages.success(request, _('Tor hidden service disabled'))

    # Update hidden service name registered with Name Services module.
    domain_removed.send_robust(
        sender='tor', domain_type='hiddenservice')

    enabled = action_utils.service_is_enabled('tor')
    is_running = action_utils.service_is_running('tor')
    (hs_enabled, hs_hostname, hs_ports) = get_hs()

    if enabled and is_running and hs_enabled and hs_hostname:
        hs_services = []
        for service in SERVICES:
            if str(service[2]) in hs_ports:
                hs_services.append(service[0])

        domain_added.send_robust(
            sender='tor', domain_type='hiddenservice',
            name=hs_hostname, description=_('Tor Hidden Service'),
            services=hs_services)

    if old_status['apt_transport_tor_enabled'] != \
       new_status['apt_transport_tor_enabled']:
        if new_status['apt_transport_tor_enabled']:
            actions.superuser_run('tor', ['enable-apt-transport-tor'])
            messages.success(request, _('Enabled package download over Tor'))
        else:
            actions.superuser_run('tor', ['disable-apt-transport-tor'])
            messages.success(request, _('Disabled package download over Tor'))
