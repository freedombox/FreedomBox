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
from django.utils.translation import ugettext as _, ugettext_lazy
import subprocess

from .forms import ConfigureForm
from plinth import actions
from plinth.errors import ActionError
from plinth.modules import upgrades

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': ugettext_lazy('Automatic Upgrades')},
              {'url': reverse_lazy('upgrades:upgrade'),
               'text': ugettext_lazy('Upgrade Packages')}]

LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades.log'
LOCK_FILE = '/var/log/dpkg/lock'


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
                            {'title': upgrades.title,
                             'description': upgrades.description,
                             'form': form,
                             'subsubmenu': subsubmenu})


def is_package_manager_busy():
    """Return whether a package manager is running."""
    try:
        subprocess.check_output(['lsof', '/var/lib/dpkg/lock'])
        return True
    except subprocess.CalledProcessError:
        return False


def get_log():
    """Return the current log for unattended upgrades."""
    try:
        with open(LOG_FILE, 'r') as file_handle:
            return file_handle.read()
    except IOError:
        return None


def upgrade(request):
    """Serve the upgrade page."""
    is_busy = is_package_manager_busy()

    if request.method == 'POST':
        try:
            actions.superuser_run('upgrades', ['run'])
            messages.success(request, _('Upgrade process started.'))
            is_busy = True
        except ActionError:
            messages.error(request, _('Starting upgrade failed.'))

    return TemplateResponse(request, 'upgrades.html',
                            {'title': upgrades.title,
                             'description': upgrades.description,
                             'subsubmenu': subsubmenu,
                             'is_busy': is_busy,
                             'log': get_log()})


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
