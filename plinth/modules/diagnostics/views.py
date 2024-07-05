# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for running diagnostics.
"""

import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from plinth import operation
from plinth.app import App
from plinth.diagnostic_check import Result
from plinth.modules import diagnostics
from plinth.setup import run_repair_on_app
from plinth.views import AppView

from .forms import ConfigureForm

logger = logging.getLogger(__name__)


class DiagnosticsView(AppView):
    """Diagnostics app page."""

    app_id = 'diagnostics'
    form_class = ConfigureForm
    template_name = 'diagnostics.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['has_diagnostics'] = False
        context['results_available'] = diagnostics.are_results_available()
        return context

    def get_initial(self):
        """Return the initial values for the form."""
        status = super().get_initial()
        status['daily_run_enabled'] = diagnostics.is_daily_run_enabled()
        status['automatic_repair'] = diagnostics.is_automatic_repair_enabled()
        return status

    def form_valid(self, form):
        """Apply the form changes."""
        old_status = form.initial
        new_status = form.cleaned_data
        updated = False

        if old_status['daily_run_enabled'] != new_status['daily_run_enabled']:
            diagnostics.set_daily_run_enabled(new_status['daily_run_enabled'])
            updated = True

        if old_status['automatic_repair'] != new_status['automatic_repair']:
            diagnostics.set_automatic_repair_enabled(
                new_status['automatic_repair'])
            updated = True

        if updated:
            messages.success(self.request, _('Configuration updated.'))

        return super().form_valid(form)


class DiagnosticsFullView(TemplateView):
    """View to run full diagnostics."""

    template_name = 'diagnostics_full.html'

    def post(self, request):
        """Start diagnostics."""
        diagnostics.start_diagnostics()
        return self.get(self, request)

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        try:
            is_task_running = bool(operation.manager.get('diagnostics-full'))
        except KeyError:
            is_task_running = False

        context = super().get_context_data(**kwargs)
        context['is_task_running'] = is_task_running
        context['results'] = diagnostics.get_results()
        context['refresh_page_sec'] = 3 if is_task_running else None
        exception = context['results'].pop('exception', None)
        if exception:
            messages.error(self.request, exception)

        return context


@require_POST
def diagnose_app(request, app_id):
    """Return diagnostics for a particular app."""
    try:
        app = App.get(app_id)
    except KeyError:
        raise Http404('App does not exist')
    app_name = app.info.name or app_id

    diagnosis = None
    diagnosis_exception = None
    try:
        diagnosis = app.diagnose()
    except Exception as exception:
        logger.exception('Error running %s diagnostics - %s', app_id,
                         exception)
        diagnosis_exception = str(exception)

    show_repair = False
    for check in diagnosis:
        if check.result in [Result.FAILED, Result.WARNING]:
            show_repair = True
            break

    return TemplateResponse(
        request, 'diagnostics_app.html', {
            'title': _('Diagnostic Test'),
            'app_id': app_id,
            'app_name': app_name,
            'results': diagnosis,
            'exception': diagnosis_exception,
            'show_repair': show_repair,
        })


@require_POST
def repair(request, app_id):
    """Try to repair failed diagnostics on an app.

    Allows apps and components to customize the repair method. Re-run setup is
    the default if not specified.
    """
    try:
        app = App.get(app_id)
    except KeyError:
        raise Http404('App does not exist')

    try:
        finish_url = reverse(f'{app_id}:index')
    except NoReverseMatch:
        # for apps like apache that don't have an index route
        finish_url = reverse('diagnostics:index')

    current_version = app.get_setup_version()
    if not current_version:
        logger.warning('App %s is not installed, cannot repair', app_id)
        message = _('App {app_id} is not installed, cannot repair')
        messages.error(request, str(message).format(app_id=app_id))
        return redirect(finish_url)

    run_repair_on_app(app_id)
    return redirect(finish_url)
