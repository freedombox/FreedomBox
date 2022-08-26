# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for security module."""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from plinth import action_utils, actions
from plinth.modules import security
from plinth.modules.upgrades import is_backports_requested
from plinth.views import AppView

from . import privileged
from .forms import SecurityForm


class SecurityAppView(AppView):
    """Show security app main page."""

    app_id = 'security'
    template_name = 'security.html'
    form_class = SecurityForm
    prefix = 'security'

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_status(self.request))
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['is_backports_requested'] = is_backports_requested()
        return context

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        _apply_changes(self.request, form.initial, form.cleaned_data)
        return super().form_valid(form)


def get_status(request):
    """Return the current status."""
    return {
        'restricted_access': privileged.get_restricted_access_enabled(),
        'fail2ban_enabled': action_utils.service_is_enabled('fail2ban')
    }


def _apply_changes(request, old_status, new_status):
    """Apply the form changes."""
    if old_status['restricted_access'] != new_status['restricted_access']:
        try:
            security.set_restricted_access(new_status['restricted_access'])
        except Exception as exception:
            messages.error(
                request,
                _('Error setting restricted access: {exception}').format(
                    exception=exception))
        else:
            messages.success(request, _('Updated security configuration'))

    if old_status['fail2ban_enabled'] != new_status['fail2ban_enabled']:
        if new_status['fail2ban_enabled']:
            actions.superuser_run('service', ['enable', 'fail2ban'])
        else:
            actions.superuser_run('service', ['disable', 'fail2ban'])


def report(request):
    """Serve the security report page."""
    apps_report = security.get_apps_report()
    return TemplateResponse(
        request, 'security_report.html', {
            'title':
                _('Security Report'),
            'freedombox_report':
                apps_report.pop('freedombox'),
            'apps_report':
                sorted(apps_report.values(), key=lambda app: app['name']),
        })
