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
Plinth module for configuring Roundcube.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
import logging

from .forms import RoundcubeForm
from plinth import actions
from plinth import package
from plinth.modules import roundcube

logger = logging.getLogger(__name__)


def before_install():
    """Preseed debconf values before the packages are installed."""
    actions.superuser_run('roundcube', ['pre-install'])


def on_install():
    """Setup Roundcube Apache configuration."""
    actions.superuser_run('roundcube', ['setup'])


@package.required(['sqlite3', 'roundcube', 'roundcube-sqlite3'],
                  before_install=before_install, on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = RoundcubeForm(request.POST, prefix='roundcube')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = RoundcubeForm(initial=status, prefix='roundcube')
    else:
        form = RoundcubeForm(initial=status, prefix='roundcube')

    return TemplateResponse(request, 'roundcube.html',
                            {'title': _('Email Client (Roundcube)'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current status."""
    return {'enabled': roundcube.is_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('roundcube', [sub_command])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
