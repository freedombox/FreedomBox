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
Plinth module to configure a Deluge web client.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _

from .forms import DelugeForm
from plinth import actions
from plinth import package
from plinth.modules import deluge


def on_install():
    """Tasks to run after package install."""
    actions.superuser_run('deluge', ['enable'])
    deluge.service.notify_enabled(None, True)


@package.required(['deluged', 'deluge-web'], on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = DelugeForm(request.POST, prefix='deluge')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = DelugeForm(initial=status, prefix='deluge')
    else:
        form = DelugeForm(initial=status, prefix='deluge')

    return TemplateResponse(request, 'deluge.html',
                            {'title': _('BitTorrent (Deluge)'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings."""
    status = {'enabled': deluge.is_enabled(),
              'is_running': deluge.is_running()}

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('deluge', [sub_command])
        deluge.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
