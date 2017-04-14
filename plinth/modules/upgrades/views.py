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
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.generic.edit import FormView
import subprocess

from .forms import ConfigureForm
from plinth import actions
from plinth.errors import ActionError
from plinth.modules import upgrades

subsubmenu = [{'url': reverse_lazy('upgrades:index'),
               'text': ugettext_lazy('Automatic Upgrades')},
              {'url': reverse_lazy('upgrades:upgrade'),
               'text': ugettext_lazy('Upgrade Packages')}]


class UpgradesConfigurationView(FormView):
    """Serve configuration page."""
    form_class = ConfigureForm
    success_url = reverse_lazy('upgrades:index')
    template_name = "upgrades_configure.html"

    def get_context_data(self, *args, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(*args, **kwargs)
        context['subsubmenu'] = subsubmenu
        context['title'] = upgrades.title
        context['description'] = upgrades.description
        return context

    def get_initial(self):
        return {'auto_upgrades_enabled': upgrades.service.is_enabled()}

    def form_valid(self, form):
        """Apply the form changes."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['auto_upgrades_enabled'] \
           != new_status['auto_upgrades_enabled']:

            try:
                if new_status['auto_upgrades_enabled']:
                    upgrades.service.enable()
                else:
                    upgrades.service.disable()
            except ActionError as exception:
                error = exception.args[2]
                messages.error(
                    self.request,
                    _('Error when configuring unattended-upgrades: {error}')
                    .format(error=error))

            if new_status['auto_upgrades_enabled']:
                messages.success(self.request, _('Automatic upgrades enabled'))
            else:
                messages.success(self.request, _('Automatic upgrades disabled'))
        else:
            messages.info(self.request, _('Settings unchanged'))

        return super().form_valid(form)


def is_package_manager_busy():
    """Return whether a package manager is running."""
    try:
        actions.superuser_run('packages', ['is-package-manager-busy'])
        return True
    except actions.ActionError:
        return False


def get_log():
    """Return the current log for unattended upgrades."""
    return actions.superuser_run('upgrades', ['get-log'])


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
