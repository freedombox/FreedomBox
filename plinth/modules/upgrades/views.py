# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for upgrades.
"""
import subprocess

from apt.cache import Cache
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView

from plinth import __version__, actions, package
from plinth.errors import ActionError
from plinth.modules import first_boot, upgrades
from plinth.views import AppView

from .forms import BackportsFirstbootForm, ConfigureForm


class UpgradesConfigurationView(AppView):
    """Serve configuration page."""
    form_class = ConfigureForm
    success_url = reverse_lazy('upgrades:index')
    template_name = "upgrades_configure.html"
    app_id = 'upgrades'

    def get_initial(self):
        return {
            'auto_upgrades_enabled': upgrades.is_enabled(),
            'dist_upgrade_enabled': upgrades.is_dist_upgrade_enabled()
        }

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['can_activate_backports'] = upgrades.can_activate_backports()
        context['is_backports_requested'] = upgrades.is_backports_requested()
        context['is_busy'] = (_is_updating()
                              or package.is_package_manager_busy())
        context['log'] = get_log()
        context['refresh_page_sec'] = 3 if context['is_busy'] else None
        context['version'] = __version__
        context['new_version'] = is_newer_version_available()
        context['os_release'] = get_os_release()
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

        if old_status['dist_upgrade_enabled'] \
           != new_status['dist_upgrade_enabled']:
            upgrades.set_dist_upgrade_enabled(
                new_status['dist_upgrade_enabled'])
            if new_status['dist_upgrade_enabled']:
                messages.success(self.request,
                                 _('Distribution upgrade enabled'))
            else:
                messages.success(self.request,
                                 _('Distribution upgrade disabled'))

        return super().form_valid(form)


def is_newer_version_available():
    """Returns whether a newer Freedombox version is available."""
    cache = Cache()
    freedombox = cache['freedombox']
    return not freedombox.candidate.is_installed


def get_os_release():
    """Returns the Debian release number and name."""
    output = 'Error: Cannot read PRETTY_NAME in /etc/os-release.'
    with open('/etc/os-release', 'r') as release_file:
        for line in release_file:
            if 'PRETTY_NAME=' in line:
                line = line.replace('"', '').strip()
                line = line.split('=')
                output = line[1]
    return output


def get_log():
    """Return the current log for unattended upgrades."""
    return actions.superuser_run('upgrades', ['get-log'])


def _is_updating():
    """Check if manually triggered update is running."""
    command = ['systemctl', 'is-active', 'freedombox-manual-upgrade']
    result = subprocess.run(command, capture_output=True, text=True)
    return str(result.stdout).startswith('activ')  # 'active' or 'activating'


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
        upgrades.set_backports_requested(True)
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
            upgrades.set_backports_requested(True)
            first_boot.mark_step_done('backports_wizard')
            return HttpResponseRedirect(reverse_lazy(first_boot.next_step()))

        if not upgrades.can_activate_backports():
            # Skip first boot step.
            upgrades.set_backports_requested(False)
            first_boot.mark_step_done('backports_wizard')
            return HttpResponseRedirect(reverse_lazy(first_boot.next_step()))

        return super().dispatch(request, *args, *kwargs)

    def get_success_url(self):
        """Return next firstboot step."""
        return reverse_lazy(first_boot.next_step())

    def form_valid(self, form):
        """Mark the first wizard step as done, save value and redirect."""
        enabled = form.cleaned_data['backports_enabled']
        upgrades.set_backports_requested(enabled)
        upgrades.setup_repositories(None)
        first_boot.mark_step_done('backports_wizard')
        return super().form_valid(form)
