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
Plinth module to configure Shaarli.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _

from .forms import ShaarliForm
from plinth import actions
from plinth import package
from plinth.modules import shaarli


@package.required(['shaarli'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ShaarliForm(request.POST, prefix='shaarli')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ShaarliForm(initial=status, prefix='shaarli')
    else:
        form = ShaarliForm(initial=status, prefix='shaarli')

    return TemplateResponse(request, 'shaarli.html',
                            {'title': _('Bookmarks (Shaarli)'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings."""
    status = {'enabled': shaarli.is_enabled()}
    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('shaarli', [sub_command])
        shaarli.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
