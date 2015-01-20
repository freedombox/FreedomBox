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
Plinth module for upgrades
"""

from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import package
from plinth.errors import ActionError


def init():
    """Initialize the module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname("Upgrades", "glyphicon-refresh",
                     "upgrades:index", 21)


@login_required
@package.required('unattended-upgrades')
def index(request):
    """Serve the index page"""
    return TemplateResponse(request, 'upgrades.html',
                            {'title': _('Package Upgrades')})


@login_required
@package.required('unattended-upgrades')
def run(request):
    """Run upgrades and show the output page"""
    output = ''
    error = ''
    try:
        output = actions.superuser_run('upgrades', ['run'])
    except ActionError as exception:
        output, error = exception.args[1:]
    except Exception as exception:
        error = str(exception)

    return TemplateResponse(request, 'upgrades_run.html',
                            {'title': _('Package Upgrades'),
                             'upgrades_output': output,
                             'upgrades__error': error})
