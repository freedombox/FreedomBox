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
from plinth import views
from plinth.errors import ActionError
from plinth.modules import upgrades

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': ugettext_lazy('Automatic Upgrades')},
              {'url': reverse_lazy('upgrades:upgrade'),
               'text': ugettext_lazy('Upgrade Packages')}]

LOG_FILE = '/var/log/unattended-upgrades/unattended-upgrades.log'
LOCK_FILE = '/var/log/dpkg/lock'


class ConfigurationView(views.ConfigurationView):
    """Serve configuration page."""
    form_class = ConfigureForm

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        if 'subsubmenu' not in kwargs:
            kwargs['subsubmenu'] = subsubmenu

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        """Return the list of template names for the view."""
        return ['upgrades_configure.html']

    def apply_changes(self, old_status, new_status):
        """Apply the form changes."""
        if old_status['auto_upgrades_enabled'] \
           == new_status['auto_upgrades_enabled']:
            return False

        try:
            upgrades.enable(new_status['auto_upgrades_enabled'])
        except ActionError as exception:
            error = exception.args[2]
            messages.error(
                self.request,
                _('Error when configuring unattended-upgrades: {error}')
                .format(error=error))
            return True

        if new_status['auto_upgrades_enabled']:
            messages.success(self.request, _('Automatic upgrades enabled'))
        else:
            messages.success(self.request, _('Automatic upgrades disabled'))

        return True


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
