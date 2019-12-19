#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app for running diagnostics.
"""

import collections
import logging
import threading

from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from plinth import module_loader
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
            'name': diagnostics.name,
            'description': diagnostics.description,
            'is_running': _running_task is not None,
            'manual_page': diagnostics.manual_page,
            'results': current_results
        })


@require_POST
def module(request, module_name):
    """Return diagnostics for a particular module."""
    try:
        module = module_loader.loaded_modules[module_name]
    except KeyError:
        raise Http404('Module does not exist or not loaded')

    results = []
    if hasattr(module, 'diagnose'):
        results = module.diagnose()

    return TemplateResponse(
        request, 'diagnostics_module.html', {
            'title': _('Diagnostic Test'),
            'module_name': module_name,
            'results': results
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
        'modules': [],
        'results': collections.OrderedDict(),
        'progress_percentage': 0
    }

    modules = []
    for module_name, module in module_loader.loaded_modules.items():
        if not hasattr(module, 'diagnose'):
            continue

        # Don't run setup on modules have not been setup yet.
        # However, run on modules that need an upgrade.
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        if not module.app.is_enabled():
            continue

        modules.append((module_name, module))
        current_results['results'][module_name] = None

    current_results['modules'] = modules
    for current_index, (module_name, module) in enumerate(modules):
        current_results['results'][module_name] = module.diagnose()
        current_results['progress_percentage'] = \
            int((current_index + 1) * 100 / len(modules))
