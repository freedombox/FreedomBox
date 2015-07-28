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

from django.http import Http404
from django.template.response import TemplateResponse
from gettext import gettext as _
import importlib

from plinth import actions
from plinth import cfg
from plinth import module_loader
from plinth.errors import ActionError


def init():
    """Initialize the module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname("Diagnostics", "glyphicon-screenshot",
                     "diagnostics:index", 30)


def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'diagnostics.html',
                            {'title': _('System Diagnostics')})


def test(request):
    """Run diagnostics and the output page"""
    output = ''
    error = ''
    try:
        output = actions.superuser_run("diagnostic-test")
    except ActionError as exception:
        output, error = exception.args[1:]
    except Exception as exception:
        error = str(exception)

    return TemplateResponse(request, 'diagnostics_test.html',
                            {'title': _('Diagnostic Test'),
                             'diagnostics_output': output,
                             'diagnostics_error': error})

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
