#
# This file is part of FreedomBox.
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
FreedomBox app for configuring Tor.
"""
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import tor
from plinth.modules.firewall.components import Firewall

from . import utils as tor_utils
from .forms import TorForm

config_process = None


def index(request):
    """Serve configuration page."""
    if config_process:
        _collect_config_result(request)

    status = tor_utils.get_status()
    form = None

    if request.method == 'POST':
        form = TorForm(request.POST, prefix='tor')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = tor_utils.get_status()
            form = TorForm(initial=status, prefix='tor')
    else:
        form = TorForm(initial=status, prefix='tor')

    return TemplateResponse(
        request, 'tor.html', {
            'name': tor.name,
            'description': tor.description,
            'clients': tor.clients,
            'manual_page': tor.manual_page,
            'status': status,
            'config_running': bool(config_process),
            'form': form,
            'firewall': tor.app.get_components_of_type(Firewall),
            'diagnostics_module_name': 'tor',
            'is_enabled': status['enabled'],
            'show_status_block': True,
            'is_running': status['is_running'],
            'icon_filename': tor.icon_filename,
        })


def _apply_changes(request, old_status, new_status):
    """Try to apply changes and handle errors."""
    try:
        __apply_changes(request, old_status, new_status)
    except ActionError as exception:
        messages.error(
            request,
            _('Action error: {0} [{1}] [{2}]').format(exception.args[0],
                                                      exception.args[1],
                                                      exception.args[2]))


def __apply_changes(request, old_status, new_status):
    """Apply the changes."""
    global config_process
    if config_process:
        # Already running a configuration task
        return

    needs_restart = False
    arguments = []

    if old_status['relay_enabled'] != new_status['relay_enabled']:
        arg_value = 'enable' if new_status['relay_enabled'] else 'disable'
        arguments.extend(['--relay', arg_value])
        needs_restart = True

    if old_status['bridge_relay_enabled'] != \
       new_status['bridge_relay_enabled']:
        arg_value = 'enable'
        if not new_status['bridge_relay_enabled']:
            arg_value = 'disable'
        arguments.extend(['--bridge-relay', arg_value])
        needs_restart = True

    if old_status['hs_enabled'] != new_status['hs_enabled']:
        arg_value = 'enable' if new_status['hs_enabled'] else 'disable'
        arguments.extend(['--hidden-service', arg_value])
        needs_restart = True

    if old_status['apt_transport_tor_enabled'] != \
       new_status['apt_transport_tor_enabled']:
        arg_value = 'disable'
        if new_status['enabled'] and new_status['apt_transport_tor_enabled']:
            arg_value = 'enable'
        arguments.extend(['--apt-transport-tor', arg_value])

    if old_status['use_upstream_bridges'] != \
       new_status['use_upstream_bridges']:
        arg_value = 'disable'
        if new_status['enabled'] and new_status['use_upstream_bridges']:
            arg_value = 'enable'
        arguments.extend(['--use-upstream-bridges', arg_value])
        needs_restart = True

    if old_status['upstream_bridges'] != new_status['upstream_bridges']:
        arguments.extend(
            ['--upstream-bridges', new_status['upstream_bridges']])
        needs_restart = True

    if old_status['enabled'] != new_status['enabled']:
        arg_value = 'enable' if new_status['enabled'] else 'disable'
        arguments.extend(['--service', arg_value])
        # XXX: Perform app enable/disable within the background process
        if new_status['enabled']:
            tor.app.enable()
        else:
            tor.app.disable()

        config_process = actions.superuser_run('tor',
                                               ['configure'] + arguments,
                                               run_in_background=True)
        return

    if arguments:
        actions.superuser_run('tor', ['configure'] + arguments)
        if not needs_restart:
            messages.success(request, _('Configuration updated.'))

    if needs_restart and new_status['enabled']:
        config_process = actions.superuser_run('tor', ['restart'],
                                               run_in_background=True)

    if not arguments:
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

    status = tor_utils.get_status()

    tor.update_hidden_service_domain(status)

    if not return_code:
        messages.success(request, _('Configuration updated.'))
    else:
        messages.error(request, _('An error occurred during configuration.'))

    config_process = None
