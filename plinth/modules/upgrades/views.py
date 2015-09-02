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

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from gettext import gettext as _

from .forms import ConfigureForm
from plinth import actions
from plinth import package
from plinth.errors import ActionError

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': _('Automatic Upgrades')},
              {'url': reverse_lazy('upgrades:upgrade'),
               'text': _('Upgrade Packages')}]


def on_install():
    """Enable automatic upgrades after install."""
    actions.superuser_run('upgrades', ['enable-auto'])


@package.required(['unattended-upgrades'], on_install=on_install)
def index(request):
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


@package.required(['unattended-upgrades'], on_install=on_install)
def upgrade(request):
    """Serve the upgrade page."""
    return TemplateResponse(request, 'upgrades.html',
                            {'title': _('Package Upgrades'),
                             'subsubmenu': subsubmenu})


@require_POST
@package.required(['unattended-upgrades'], on_install=on_install)
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
