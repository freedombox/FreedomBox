# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for running diagnostics.
"""

import collections
import importlib
import logging
import threading

from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from plinth.app import App
from plinth.modules import diagnostics

logger = logging.Logger(__name__)

current_results = {}

_running_task = None


def index(request):
    """Serve the index page"""
    if request.method == 'POST' and not _running_task:
        _start_task()

    return TemplateResponse(
        request, 'diagnostics.html', {
            'app_info': diagnostics.app.info,
            'is_running': _running_task is not None,
            'results': current_results
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


def _start_task():
    """Start the run task in a separate thread."""
    global _running_task
    if _running_task:
        raise Exception('Task already running')

    _running_task = threading.Thread(
        target=_run_on_all_enabled_modules_wrapper)
    _running_task.start()


def _run_on_all_enabled_modules_wrapper():
    """Wrapper over actual task to catch exceptions."""
    try:
        run_on_all_enabled_modules()
    except Exception as exception:
        logger.exception('Error running diagnostics - %s', exception)
        current_results['error'] = str(exception)

    global _running_task
    _running_task = None


def run_on_all_enabled_modules():
    """Run diagnostics on all the enabled modules and store the result."""
    global current_results
    current_results = {
        'apps': [],
        'results': collections.OrderedDict(),
        'progress_percentage': 0
    }

    apps = []
    for app in App.list():
        # XXX: Implement more cleanly.
        # Don't run diagnostics on apps have not been setup yet.
        # However, run on apps that need an upgrade.
        module = importlib.import_module(app.__class__.__module__)
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        if not app.is_enabled():
            continue

        if not app.has_diagnostics():
            continue

        apps.append((app.app_id, app))
        current_results['results'][app.app_id] = None

    current_results['apps'] = apps
    for current_index, (app_id, app) in enumerate(apps):
        current_results['results'][app_id] = app.diagnose()
        current_results['progress_percentage'] = \
            int((current_index + 1) * 100 / len(apps))
