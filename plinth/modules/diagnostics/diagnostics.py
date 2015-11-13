#
# This file is part of Plinth.
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
Plinth module for running diagnostics
"""

import collections
from django.http import Http404
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext_lazy as _
import importlib
import logging
import threading

from plinth import cfg
from plinth import module_loader


logger = logging.Logger(__name__)

current_results = {}

_running_task = None


def init():
    """Initialize the module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Diagnostics'), 'glyphicon-screenshot',
                     'diagnostics:index', 30)


def index(request):
    """Serve the index page"""
    if request.method == 'POST' and not _running_task:
        _start_task()

    return TemplateResponse(request, 'diagnostics.html',
                            {'title': _('System Diagnostics'),
                             'is_running': _running_task is not None,
                             'results': current_results})


@require_POST
def module(request, module_name):
    """Return diagnostics for a particular module."""
    found = False
    for module_import_path in module_loader.loaded_modules:
        if module_name == module_import_path.split('.')[-1]:
            found = True
            break

    if not found:
        raise Http404('Module does not exist or not loaded')

    loaded_module = importlib.import_module(module_import_path)
    results = []
    if hasattr(loaded_module, 'diagnose'):
        results = loaded_module.diagnose()

    return TemplateResponse(request, 'diagnostics_module.html',
                            {'title': _('Diagnostic Test'),
                             'module_name': module_name,
                             'results': results})


def _start_task():
    """Start the run task in a separate thread."""
    if _running_task:
        raise Exception('Task already running')

    global _running_task
    _running_task = threading.Thread(target=_run_on_all_modules_wrapper)
    _running_task.start()


def _run_on_all_modules_wrapper():
    """Wrapper over actual task to catch exceptions."""
    try:
        run_on_all_modules()
    except Exception as exception:
        logger.exception('Error running diagnostics - %s', exception)
        current_results['error'] = str(exception)

    global _running_task
    _running_task = None


def run_on_all_modules():
    """Run diagnostics on all modules and store the result."""
    global current_results
    current_results = {'modules': [],
                       'results': collections.OrderedDict(),
                       'progress_percentage': 0}

    modules = []
    for module_import_path in module_loader.loaded_modules:
        loaded_module = importlib.import_module(module_import_path)
        if not hasattr(loaded_module, 'diagnose'):
            continue

        module_name = module_import_path.split('.')[-1]
        modules.append((module_name, loaded_module))
        current_results['results'][module_name] = None

    current_results['modules'] = modules
    for current_index, (module_name, loaded_module) in enumerate(modules):
        current_results['results'][module_name] = loaded_module.diagnose()
        current_results['progress_percentage'] = \
            int((current_index + 1) * 100 / len(modules))
