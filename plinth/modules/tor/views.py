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
from plinth.errors import ActionError
from plinth.modules import tor
from plinth.modules.names import SERVICES
from plinth.signals import domain_added, domain_removed

config_process = None


def index(request):
    """Serve configuration page."""
    if config_process:
        _collect_config_result(request)

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
                            {'title': tor.title,
                             'description': tor.description,
                             'status': status,
                             'config_running': bool(config_process),
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
    global config_process
    if config_process:
        # Already running a configuration task
        return

    arguments = []

    if old_status['enabled'] != new_status['enabled']:
        arg_value = 'enable' if new_status['enabled'] else 'disable'
        arguments.extend(['--service', arg_value])

    if old_status['hs_enabled'] != new_status['hs_enabled']:
        arg_value = 'enable' if new_status['hs_enabled'] else 'disable'
        arguments.extend(['--hidden-service', arg_value])

    if old_status['apt_transport_tor_enabled'] != \
       new_status['apt_transport_tor_enabled']:
        arg_value = 'disable'
        if new_status['enabled'] and new_status['apt_transport_tor_enabled']:
            arg_value = 'enable'
        arguments.extend(['--apt-transport-tor', arg_value])

    if arguments:
        config_process = actions.superuser_run(
            'tor', ['configure'] + arguments, async=True)
    else:
        messages.info(request, _('Setting unchanged'))


def _collect_config_result(request):
    """Handle config process completion."""
    global config_process
    if not config_process:
        return

    return_code = config_process.poll()

    # Config process is not complete yet
    if return_code is None:
        return

    status = tor.get_status()

    tor.socks_service.notify_enabled(None, status['enabled'])
    tor.bridge_service.notify_enabled(None, status['enabled'])

    # Update hidden service name registered with Name Services module.
    domain_removed.send_robust(
        sender='tor', domain_type='hiddenservice')

    if status['enabled'] and status['is_running'] and \
       status['hs_enabled'] and status['hs_hostname']:
        hs_services = []
        for service in SERVICES:
            if str(service[2]) in status['hs_ports']:
                hs_services.append(service[0])

        domain_added.send_robust(
            sender='tor', domain_type='hiddenservice',
            name=status['hs_hostname'], description=_('Tor Hidden Service'),
            services=hs_services)

    if not return_code:
        messages.success(request, _('Configuration updated.'))
    else:
        messages.error(request, _('An error occurred during configuration.'))

    config_process = None
