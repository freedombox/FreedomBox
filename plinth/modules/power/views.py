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

from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from plinth import actions


def index(request):
    """Serve power controls page."""
    return TemplateResponse(request, 'power.html',
                            {'title': _('Power Control')})


def reboot(request):
    """Serve reboot confirmation page."""
    return TemplateResponse(request, 'power_reboot.html',
                            {'title': _('Power Control')})


def reboot_now(request):
    """Reboot the system."""
    actions.superuser_run('power', ['reboot'])


def shutdown(request):
    """Serve shutdown confirmation page."""
    return TemplateResponse(request, 'power_shutdown.html',
                            {'title': _('Power Control')})


def shutdown_now(request):
    """Shutdown the system."""
    actions.superuser_run('power', ['shutdown'])
