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
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.http import require_POST

from .forms import ConfigureForm
from plinth import actions
from plinth import package
from plinth.errors import ActionError

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': ugettext_lazy('Automatic Upgrades')},
              {'url': reverse_lazy('upgrades:upgrade'),
               'text': ugettext_lazy('Upgrade Packages')}]

upgrade_process = None


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
    result = _collect_upgrade_result(request)

    return TemplateResponse(request, 'upgrades.html',
                            {'title': _('Package Upgrades'),
                             'subsubmenu': subsubmenu,
                             'running': bool(upgrade_process),
                             'result': result})


@require_POST
@package.required(['unattended-upgrades'], on_install=on_install)
def run(_):
    """Start the upgrade process."""
    global upgrade_process
    if not upgrade_process:
        upgrade_process = actions.superuser_run(
            'upgrades', ['run'], async=True)

    return redirect('upgrades:upgrade')


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
            request, _('Error when configuring unattended-upgrades: {error}')
            .format(error=error))
        return

    if option == 'enable-auto':
        messages.success(request, _('Automatic upgrades enabled'))
    else:
        messages.success(request, _('Automatic upgrades disabled'))


def _collect_upgrade_result(request):
    """Handle upgrade process completion."""
    global upgrade_process
    if not upgrade_process:
        return

    return_code = upgrade_process.poll()

    # Upgrade process is not complete yet
    if return_code is None:
        return

    output, error = upgrade_process.communicate()
    output, error = output.decode(), error.decode()

    if not return_code:
        messages.success(request, _('Upgrade completed.'))
    else:
        messages.error(request, _('Upgrade failed.'))

    upgrade_process = None

    return {'return_code': return_code,
            'output': output,
            'error': error}
