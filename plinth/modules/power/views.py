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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for power module.
"""

from django.forms import Form
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.modules import power


def index(request):
    """Serve power controls page."""
    return TemplateResponse(request, 'power.html',
                            {'title': power.title,
                             'description': power.description})


def restart(request):
    """Serve start confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['restart'], async=True)
        return redirect(reverse('apps'))
    else:
        form = Form(prefix='power')

    return TemplateResponse(request, 'power_restart.html',
                            {'title': _('Power'),
                             'form': form})


def shutdown(request):
    """Serve shutdown confirmation page."""
    form = None

    if request.method == 'POST':
        actions.superuser_run('power', ['shutdown'], async=True)
        return redirect(reverse('apps'))
    else:
        form = Form(prefix='power')

    return TemplateResponse(request, 'power_shutdown.html',
                            {'title': _('Power'),
                             'form': form})
