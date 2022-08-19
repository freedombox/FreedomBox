# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for power module.
"""

from django.forms import Form
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from plinth import actions
from plinth import app as app_module
from plinth import package
from plinth.views import AppView


class PowerAppView(AppView):
    """Show power app main page."""

    app_id = 'power'
    template_name = 'power.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['pkg_manager_is_busy'] = package.is_package_manager_busy()
        return context


def restart(request):
    """Serve start confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['restart'], run_in_background=True)
        return redirect(reverse('apps'))

    app = app_module.App.get('power')
    form = Form(prefix='power')
    return TemplateResponse(
        request, 'power_restart.html', {
            'title': app.info.name,
            'form': form,
            'manual_page': app.info.manual_page,
            'pkg_manager_is_busy': package.is_package_manager_busy()
        })


def shutdown(request):
    """Serve shutdown confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['shutdown'], run_in_background=True)
        return redirect(reverse('apps'))

    app = app_module.App.get('power')
    form = Form(prefix='power')
    return TemplateResponse(
        request, 'power_shutdown.html', {
            'title': app.info.name,
            'form': form,
            'manual_page': app.info.manual_page,
            'pkg_manager_is_busy': package.is_package_manager_busy()
        })
