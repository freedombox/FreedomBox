# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for upgrades.
"""

import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView

from plinth import actions, kvstore, package
from plinth.errors import ActionError
from plinth.modules import first_boot, upgrades
from plinth.views import AppView

from .forms import BackportsFirstbootForm, ConfigureForm

logger = logging.getLogger(__name__)


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
        context['is_backports_enabled'] = upgrades.is_backports_enabled()
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
        kvstore.set(upgrades.BACKPORTS_ENABLED_KEY, True)
        upgrades.setup_repositories(None)
        messages.success(request, _('Frequent feature updates activated.'))

    return redirect(reverse_lazy('upgrades:index'))


class BackportsFirstbootView(FormView):
    """View to configure backports during first boot wizard."""
    template_name = 'backports-firstboot.html'
    form_class = BackportsFirstbootForm

    def dispatch(self, request, *args, **kwargs):
        """Show backports configuration form only if it can be activated."""
        if upgrades.is_backports_enabled():
            # Backports is already enabled. Record this preference and
            # skip first boot step.
            kvstore.set(upgrades.BACKPORTS_ENABLED_KEY, True)
            first_boot.mark_step_done('backports_wizard')
            return HttpResponseRedirect(reverse_lazy(first_boot.next_step()))

        if not upgrades.can_activate_backports():
            # Skip first boot step.
            first_boot.mark_step_done('backports_wizard')
            return HttpResponseRedirect(reverse_lazy(first_boot.next_step()))

        return super().dispatch(request, *args, *kwargs)

    def get_initial(self):
        """Get initial form data."""
        return {
            'backports_enabled':
                kvstore.get_default(upgrades.BACKPORTS_ENABLED_KEY, True)
        }

    def get_success_url(self):
        """Return next firstboot step."""
        return reverse_lazy(first_boot.next_step())

    def form_valid(self, form):
        """Mark the first wizard step as done, save value and redirect."""
        enabled = form.cleaned_data['backports_enabled']
        kvstore.set(upgrades.BACKPORTS_ENABLED_KEY, enabled)
        if enabled:
            upgrades.setup_repositories(None)
            logger.info('Backports enabled.')
        else:
            logger.info('Backports not enabled.')

        first_boot.mark_step_done('backports_wizard')
        return super().form_valid(form)
