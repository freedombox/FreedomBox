# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for running diagnostics.
"""

import logging

from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from plinth import operation
from plinth.app import App
from plinth.modules import diagnostics
from plinth.views import AppView

from .check import Result

logger = logging.getLogger(__name__)


class DiagnosticsView(AppView):
    """Diagnostics app page."""

    app_id = 'diagnostics'
    template_name = 'diagnostics.html'

    def post(self, request):
        """Start diagnostics."""
        diagnostics.start_diagnostics()
        return HttpResponseRedirect(reverse('diagnostics:index'))

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['has_diagnostics'] = False
        context['results_available'] = diagnostics.are_results_available()
        return context


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

    show_rerun_setup = False
    for check in diagnosis:
        if check.result in [Result.FAILED, Result.WARNING]:
            show_rerun_setup = True
            break

    return TemplateResponse(
        request, 'diagnostics_app.html', {
            'title': _('Diagnostic Test'),
            'app_id': app_id,
            'app_name': app_name,
            'results': diagnosis,
            'exception': diagnosis_exception,
            'show_rerun_setup': show_rerun_setup,
        })
