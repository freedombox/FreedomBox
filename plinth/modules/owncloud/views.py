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
Plinth module for configuring ownCloud.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .forms import OwnCloudForm
from plinth import actions
from plinth.modules import owncloud


def index(request):
    """Serve the ownCloud configuration page"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = OwnCloudForm(request.POST, prefix='owncloud')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = OwnCloudForm(initial=status, prefix='owncloud')
    else:
        form = OwnCloudForm(initial=status, prefix='owncloud')

    return TemplateResponse(request, 'owncloud.html',
                            {'title': owncloud.title,
                             'description': owncloud.description,
                             'form': form})


def get_status():
    """Return the current status"""
    return {'enabled': owncloud.is_enabled()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes"""
    if old_status['enabled'] == new_status['enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['enabled']:
        messages.success(request, _('ownCloud enabled'))
        option = 'enable'
    else:
        messages.success(request, _('ownCloud disabled'))
        option = 'noenable'

    actions.superuser_run('owncloud-setup', [option])

    # Send a signal to other modules that the service is
    # enabled/disabled
    owncloud.service.notify_enabled(None, new_status['enabled'])
