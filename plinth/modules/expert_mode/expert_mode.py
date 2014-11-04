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

from plinth import cfg
from plinth.modules.lib.auth import get_or_create_group


class ExpertsForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure expert mode"""
    expert_mode = forms.BooleanField(
        label=_('Expert Mode'), required=False)


def init():
    """Initialize the module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Expert Mode'), 'icon-cog', 'expert_mode:index', 10)


@login_required
def index(request):
    """Serve the configuration form"""
    status = get_status(request)

    form = None

    if request.method == 'POST':
        form = ExpertsForm(request.POST, prefix='experts')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, form.cleaned_data)
            status = get_status(request)
            form = ExpertsForm(initial=status, prefix='experts')
    else:
        form = ExpertsForm(initial=status, prefix='experts')

    return TemplateResponse(request, 'expert_mode.html',
                            {'title': _('Expert Mode'),
                             'form': form})


def get_status(request):
    """Return the current status"""
    return {'expert_mode': request.user.groups.filter(name='Expert').exists()}


def _apply_changes(request, new_status):
    """Apply expert mode configuration"""
    message = (messages.info, _('Settings unchanged'))

    expert_group = get_or_create_group('Expert')
    if new_status['expert_mode']:
        if not expert_group in request.user.groups.all():
            request.user.groups.add(expert_group)
            message = (messages.success, _('Expert mode enabled'))
    else:
        if expert_group in request.user.groups.all():
            request.user.groups.remove(expert_group)
            message = (messages.success, _('Expert mode disabled'))

    message[0](request, message[1])
