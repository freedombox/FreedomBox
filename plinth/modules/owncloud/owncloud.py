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

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import package
from plinth import service


SERVICE = None


class OwnCloudForm(forms.Form):  # pylint: disable-msg=W0232
    """ownCloud configuration form"""
    enabled = forms.BooleanField(label=_('Enable ownCloud'), required=False)


def init():
    """Initialize the ownCloud module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('ownCloud', 'glyphicon-picture', 'owncloud:index', 35)

    status = get_status()

    global SERVICE  # pylint: disable-msg=W0603
    SERVICE = service.Service('owncloud', _('ownCloud'), ['http', 'https'],
                              is_external=True, enabled=status['enabled'])


@login_required
@package.required('postgresql', 'php5-pgsql', 'owncloud')
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
                            {'title': _('ownCloud'),
                             'form': form})


def get_status():
    """Return the current status"""
    output = actions.run('owncloud-setup', 'status')
    return {'enabled': 'enable' in output.split()}


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

    actions.superuser_run('owncloud-setup', [option], async=True)

    # Send a signal to other modules that the service is
    # enabled/disabled
    SERVICE.notify_enabled(None, new_status['enabled'])
