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
Plinth module to configure a BitTorrent web client (deluge-web)
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from gettext import gettext as _

from .forms import BitTorrentForm
from plinth import actions
from plinth import package


@login_required
@package.required(['deluged', 'deluge-web'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = BitTorrentForm(request.POST, prefix='bittorrent')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = BitTorrentForm(initial=status, prefix='bittorrent')
    else:
        form = BitTorrentForm(initial=status, prefix='bittorrent')

    return TemplateResponse(request, 'bittorrent.html',
                            {'title': _('BitTorrent (Deluge)'),
                             'status': status,
                             'form': form})


@login_required
@require_POST
def start(request):
    """Start deluge-web."""
    actions.run('bittorrent', ['start'])
    return redirect(reverse_lazy('bittorrent:index'))


@login_required
@require_POST
def stop(request):
    """Stop deluge-web."""
    actions.run('bittorrent', ['stop'])
    return redirect(reverse_lazy('bittorrent:index'))


def get_status():
    """Get the current settings."""
    output = actions.run('bittorrent', ['get-enabled'])
    enabled = (output.strip() == 'yes')

    output = actions.run('bittorrent', ['is-running'])
    is_running = ('yes' in output.strip())

    status = {'enabled': enabled,
              'is_running': is_running}

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('bittorrent', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
