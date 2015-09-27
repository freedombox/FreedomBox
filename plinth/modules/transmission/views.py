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

"""
Plinth module for configuring Transmission Server
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _
import json
import logging
import socket

from .forms import TransmissionForm
from plinth import actions
from plinth import package
from plinth.modules import transmission

logger = logging.getLogger(__name__)

TRANSMISSION_CONFIG = '/etc/transmission-daemon/settings.json'


def on_install():
    """Enable transmission as soon as it is installed."""
    actions.superuser_run('transmission', ['enable'])
    transmission.service.notify_enabled(None, True)


@package.required(['transmission-daemon'], on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = TransmissionForm(request.POST, prefix='transmission')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = TransmissionForm(initial=status, prefix='transmission')
    else:
        form = TransmissionForm(initial=status, prefix='transmission')

    return TemplateResponse(request, 'transmission.html',
                            {'title': _('BitTorrent (Transmission)'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings from Transmission server."""
    configuration = open(TRANSMISSION_CONFIG, 'r').read()
    status = json.loads(configuration)
    status = {key.translate(str.maketrans({'-': '_'})): value
              for key, value in status.items()}
    status['enabled'] = transmission.is_enabled()
    status['is_running'] = transmission.is_running()
    status['hostname'] = socket.gethostname()

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes"""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('transmission', [sub_command])
        transmission.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if old_status['download_dir'] != new_status['download_dir'] or \
       old_status['rpc_username'] != new_status['rpc_username'] or \
       old_status['rpc_password'] != new_status['rpc_password']:
        new_configuration = {
            'download-dir': new_status['download_dir'],
            'rpc-username': new_status['rpc_username'],
            'rpc-password': new_status['rpc_password'],
        }

        actions.superuser_run('transmission', ['merge-configuration'],
                              input=json.dumps(new_configuration).encode())
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
