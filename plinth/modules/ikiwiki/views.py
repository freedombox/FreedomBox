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
Plinth module for configuring ikiwiki
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _

from .forms import IkiwikiForm
from plinth import actions
from plinth import package
from plinth.modules import ikiwiki


@login_required
@package.required(['ikiwiki'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = IkiwikiForm(request.POST, prefix='ikiwiki')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = IkiwikiForm(initial=status, prefix='ikiwiki')
    else:
        form = IkiwikiForm(initial=status, prefix='ikiwiki')

    return TemplateResponse(request, 'ikiwiki.html',
                            {'title': _('Wiki'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current setting."""
    output = actions.run('ikiwiki', ['get-enabled'])
    enabled = (output.strip() == 'yes')
    return {'enabled': enabled}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('ikiwiki', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
