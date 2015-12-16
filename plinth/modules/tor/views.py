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
Plinth module for configuring Tor.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import TorForm
from plinth import actions
from plinth import package
from plinth.errors import ActionError
from plinth.modules import tor
from plinth.modules.names import SERVICES
from plinth.signals import domain_added, domain_removed


def on_install():
    """Setup Tor configuration as soon as it is installed."""
    actions.superuser_run('tor', ['setup'])
    actions.superuser_run('tor', ['enable-apt-transport-tor'])
    tor.socks_service.notify_enabled(None, True)
    tor.bridge_service.notify_enabled(None, True)


@package.required(['tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy',
                   'apt-transport-tor'],
                  on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = tor.get_status()

    form = None

    if request.method == 'POST':
        form = TorForm(request.POST, prefix='tor')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = tor.get_status()
            form = TorForm(initial=status, prefix='tor')
    else:
        form = TorForm(initial=status, prefix='tor')

    return TemplateResponse(request, 'tor.html',
                            {'title': _('Tor Control Panel'),
                             'status': status,
                             'form': form})


def _apply_changes(request, old_status, new_status):
    """Try to apply changes and handle errors."""
    try:
        __apply_changes(request, old_status, new_status)
    except ActionError as exception:
        messages.error(request, _('Action error: {0} [{1}] [{2}]').format(
            exception.args[0], exception.args[1], exception.args[2]))


def __apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('tor', [sub_command])
        tor.socks_service.notify_enabled(None, new_status['enabled'])
        tor.bridge_service.notify_enabled(None, new_status['enabled'])
        modified = True

    if old_status['hs_enabled'] != new_status['hs_enabled']:
        sub_command = 'enable-hs' if new_status['hs_enabled'] else 'disable-hs'
        actions.superuser_run('tor', [sub_command])
        modified = True

    if old_status['apt_transport_tor_enabled'] != \
       new_status['apt_transport_tor_enabled']:
        sub_command = 'enable-apt-transport-tor' \
                      if new_status['apt_transport_tor_enabled'] \
                         else 'disable-apt-transport-tor'
        actions.superuser_run('tor', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))

    # Update hidden service name registered with Name Services module.
    domain_removed.send_robust(
        sender='tor', domain_type='hiddenservice')

    (hs_enabled, hs_hostname, hs_ports) = tor.get_hs()
    if tor.is_enabled() and tor.is_running() and hs_enabled and hs_hostname:
        hs_services = []
        for service in SERVICES:
            if str(service[2]) in hs_ports:
                hs_services.append(service[0])

        domain_added.send_robust(
            sender='tor', domain_type='hiddenservice',
            name=hs_hostname, description=_('Tor Hidden Service'),
            services=hs_services)
