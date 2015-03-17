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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for upgrades
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import package
from plinth.errors import ActionError

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': _('Upgrade Packages')},
              {'url': reverse_lazy('upgrades:configure'),
               'text': _('Automatic Upgrades')}]


def init():
    """Initialize the module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Software Upgrades'), 'glyphicon-refresh',
                     'upgrades:index', 21)


@login_required
@package.required(['unattended-upgrades'])
def index(request):
    """Serve the index page."""
    return TemplateResponse(request, 'upgrades.html',
                            {'title': _('Package Upgrades'),
                             'subsubmenu': subsubmenu})


@login_required
@require_POST
@package.required(['unattended-upgrades'])
def run(request):
    """Run upgrades and show the output page."""
    output = ''
    error = ''
    try:
        output = actions.superuser_run('upgrades', ['run'])
    except ActionError as exception:
        output, error = exception.args[1:]
    except Exception as exception:
        error = str(exception)

    return TemplateResponse(request, 'upgrades_run.html',
                            {'title': _('Package Upgrades'),
                             'subsubmenu': subsubmenu,
                             'upgrades_output': output,
                             'upgrades_error': error})


class ConfigureForm(forms.Form):
    """Configuration form to enable/disable automatic upgrades."""
    auto_upgrades_enabled = forms.BooleanField(
        label=_('Enable automatic upgrades'), required=False,
        help_text=_('When enabled, the unattended-upgrades program will be \
run once per day. It will attempt to perform any package upgrades that are \
available.'))


@login_required
@package.required(['unattended-upgrades'])
def configure(request):
    """Serve the configuration form."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='upgrades')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='upgrades')
    else:
        form = ConfigureForm(initial=status, prefix='upgrades')

    return TemplateResponse(request, 'upgrades_configure.html',
                            {'title': _('Automatic Upgrades'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def get_status():
    """Return the current status."""
    output = actions.run('upgrades', ['check-auto'])
    return {'auto_upgrades_enabled': 'True' in output.split()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes."""
    if old_status['auto_upgrades_enabled'] \
       == new_status['auto_upgrades_enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['auto_upgrades_enabled']:
        option = 'enable-auto'
    else:
        option = 'disable-auto'

    try:
        actions.superuser_run('upgrades', [option])
    except ActionError as exception:
        error = exception.args[2]
        messages.error(
            request, _('Error when configuring unattended-upgrades: %s') %
            error)
        return

    if option == 'enable-auto':
        messages.success(request, _('Automatic upgrades enabled'))
    else:
        messages.success(request, _('Automatic upgrades disabled'))
