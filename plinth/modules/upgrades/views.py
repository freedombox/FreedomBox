# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for upgrades.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _

from plinth import actions, package
from plinth.errors import ActionError
from plinth.modules import upgrades
from plinth.views import AppView

from .forms import ConfigureForm


class UpgradesConfigurationView(AppView):
    """Serve configuration page."""
    form_class = ConfigureForm
    success_url = reverse_lazy('upgrades:index')
    template_name = "upgrades_configure.html"
    app_id = 'upgrades'

    def get_initial(self):
        return {'auto_upgrades_enabled': upgrades.is_enabled()}

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['can_activate_backports'] = upgrades.can_activate_backports()
        context['is_busy'] = package.is_package_manager_busy()
        context['log'] = get_log()
        context['refresh_page_sec'] = 3 if context['is_busy'] else None
        return context

    def form_valid(self, form):
        """Apply the form changes."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['auto_upgrades_enabled'] \
           != new_status['auto_upgrades_enabled']:

            try:
                if new_status['auto_upgrades_enabled']:
                    upgrades.enable()
                else:
                    upgrades.disable()
            except ActionError as exception:
                error = exception.args[2]
                messages.error(
                    self.request,
                    _('Error when configuring unattended-upgrades: {error}').
                    format(error=error))

            if new_status['auto_upgrades_enabled']:
                messages.success(self.request, _('Automatic upgrades enabled'))
            else:
                messages.success(self.request,
                                 _('Automatic upgrades disabled'))

        return super().form_valid(form)


def get_log():
    """Return the current log for unattended upgrades."""
    return actions.superuser_run('upgrades', ['get-log'])


def upgrade(request):
    """Serve the upgrade page."""
    if request.method == 'POST':
        try:
            actions.superuser_run('upgrades', ['run'])
            messages.success(request, _('Upgrade process started.'))
        except ActionError:
            messages.error(request, _('Starting upgrade failed.'))

    return redirect(reverse_lazy('upgrades:index'))


def activate_backports(request):
    """Activate backports."""
    if request.method == 'POST':
        upgrades.setup_repositories(None)
        messages.success(request, _('Frequent feature updates activated.'))

    return redirect(reverse_lazy('upgrades:index'))
