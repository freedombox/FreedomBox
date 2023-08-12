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

from plinth.app import App
from plinth.modules import diagnostics
from plinth.views import AppView

logger = logging.getLogger(__name__)


class DiagnosticsView(AppView):
    """Diagnostics app page."""

    app_id = 'diagnostics'
    template_name = 'diagnostics.html'

    def post(self, request):
        """Start diagnostics."""
        with diagnostics.running_task_lock:
            if not diagnostics.running_task:
                diagnostics.start_task()

        return HttpResponseRedirect(reverse('diagnostics:index'))

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        with diagnostics.running_task_lock:
            is_task_running = diagnostics.running_task is not None

        with diagnostics.results_lock:
            results = diagnostics.current_results

        context = super().get_context_data(**kwargs)
        context['has_diagnostics'] = False
        context['is_task_running'] = is_task_running
        context['results'] = results
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

    return TemplateResponse(
        request, 'diagnostics_app.html', {
            'title': _('Diagnostic Test'),
            'app_name': app_name,
            'results': diagnosis,
            'exception': diagnosis_exception,
        })
