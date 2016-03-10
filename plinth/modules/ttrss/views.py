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
Plinth module for configuring News Feed Reader (Tiny Tiny RSS)
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from plinth import actions
from plinth import package
from plinth.modules import ttrss
from .forms import TtrssForm

logger = logging.getLogger(__name__)


@package.required(['tt-rss'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = TtrssForm(request.POST, prefix='ttrss')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = TtrssForm(initial=status, prefix='ttrss')
    else:
        form = TtrssForm(initial=status, prefix='ttrss')

    return TemplateResponse(request, 'ttrss.html',
                            {'title': _('News Feed Reader (Tiny Tiny RSS)'),
                             'status': status,
                             'form': form})

def get_status():
    """Get the current status."""
    return {'enabled': ttrss.is_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('ttrss', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))




