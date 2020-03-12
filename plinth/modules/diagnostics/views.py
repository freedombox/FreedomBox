# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for running diagnostics.
"""

from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from plinth.app import App
from plinth.modules import diagnostics


def index(request):
    """Serve the index page"""
    if request.method == 'POST' and not diagnostics.running_task:
        diagnostics.start_task()

    return TemplateResponse(
        request, 'diagnostics.html', {
            'app_info': diagnostics.app.info,
            'is_running': diagnostics.running_task is not None,
            'results': diagnostics.current_results
        })


@require_POST
def diagnose_app(request, app_id):
    """Return diagnostics for a particular app."""
    try:
        app = App.get(app_id)
    except KeyError:
        raise Http404('App does not exist')

    return TemplateResponse(request, 'diagnostics_app.html', {
        'title': _('Diagnostic Test'),
        'app_id': app_id,
        'results': app.diagnose()
    })
